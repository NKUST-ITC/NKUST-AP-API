import hashlib
import pickle
import json
import redis
import requests

from crawler import webap_crawler
from utils import error_code
from utils import config
from utils.config import REDIS_URL
from cache import parse

red_string = redis.StrictRedis.from_url(
    url=REDIS_URL, db=4, charset="utf-8", decode_responses=True)
red_bin = redis.StrictRedis.from_url(url=REDIS_URL, db=3)


def login(username, password):
    """login to webap
    If user was logged in before JWT_EXPIRE_TIME, redis will save
    SHA-256(username+password) to check user in  JWT_EXPIRE_TIME.
    Avoid multiple login in to NKUST server in short time.

    Args:
        username ([str]): webap username
        password ([str]): webap password

    Returns:
        [int]: login status. utils/error_code.py
                CACHE_WENAP_LOGIN_SUCCESS (110)
                CACHE_WEBAP_LOGIN_FAIL (111)
                CACHE_WEBAP_SERVER_ERROR (112)
                CACHE_WEBAP_ERROR (113)
    """
    # check username and password without use NKUST server
    if red_string.exists('api_login_%s' % username):
        s = hashlib.sha256()
        s.update((username+password).encode('utf-8'))
        user_hash = s.hexdigest()
        if red_string.get('api_login_%s' % username) == user_hash:

            # check webap cookie exist
            if red_bin.exists('webap_cookie_%s' % username):
                return error_code.CACHE_WENAP_LOGIN_SUCCESS

    session = requests.session()

    login_status = webap_crawler.login(
        session=session, username=username, password=password)

    if login_status == error_code.WENAP_LOGIN_SUCCESS:
        # save user hash to redis
        s = hashlib.sha256()
        s.update((username+password).encode('utf-8'))
        user_hash = s.hexdigest()
        red_string.set(name='api_login_%s' % username,
                       value=user_hash, ex=config.CACHE_USER_HASH_EXPIRE_TIME)

        # save cookie to redis
        red_bin.set(name='webap_cookie_%s' %
                    username, value=pickle.dumps(session.cookies), ex=config.CACHE_WEBAP_COOKIE_EXPIRE_TIME)

        return error_code.CACHE_WENAP_LOGIN_SUCCESS

    elif login_status == error_code.WEBAP_LOGIN_FAIL:
        return error_code.CACHE_WEBAP_LOGIN_FAIL
    elif login_status == error_code.WEBAP_SERVER_ERROR:
        return error_code.CACHE_WEBAP_SERVER_ERROR
    elif login_status == error_code.WEBAP_ERROR:
        return error_code.CACHE_WEBAP_ERROR

    return error_code.CACHE_WEBAP_ERROR


def user_info(username, password):
    """get user info 

    Args:
        username ([str]): NKUST webap username
        password ([str]): NKUST webap password

    Returns:
        [dict]: user info

        in any error
        [int]: CACHE_AP_QUERY_USERINFO_ERROR
               CACHE_WEBAP_LOGIN_FAIL
               CACHE_WEBAP_SERVER_ERROR
               CACHE_WEBAP_ERROR
               USER_INFO_PARSE_ERROR
               USER_INFO_ERROR
    """
    # check login
    login_status = login(username=username, password=password)

    if login_status == error_code.CACHE_WENAP_LOGIN_SUCCESS:
        res = cache_ap_query(username=username, qid='ag003')
        if res == False:
            return error_code.CACHE_AP_QUERY_USERINFO_ERROR
        user_info_parse = parse.userinfo(html=res)
        if user_info_parse == False:
            return error_code.USER_INFO_PARSE_ERROR
        return user_info_parse
    else:
        return login_status
    return error_code.USER_INFO_ERROR


def semesters():
    """/user/semesters
    In this function, without use cache_ap_query
    use webap_crawler.query and use GUEST account.

    Returns:
        [str]: result type is json 
            Why don't use dict?
            redis can't save dict :P

        error:
            [int] 
                SEMESTERS_QUERY_ERROR
                WEBAP_ERROR

    """
    if red_string.exists('semesters'):
        return red_string.get('semesters')
    session = requests.session()
    login_status = webap_crawler.login(session=session,
                                       username=config.AP_GUEST_ACCOUNT,
                                       password=config.AP_GUEST_PASSWORD)

    if login_status == error_code.WENAP_LOGIN_SUCCESS:
        query_res = webap_crawler.query(session=session, qid='ag304_01')
        if query_res == False:
            return error_code.SEMESTERS_QUERY_ERROR
        elif isinstance(query_res, requests.models.Response):
            semesters_data = json.dumps(parse.semesters(query_res.text))
            red_string.set(name='semesters',
                           value=semesters_data,
                           ex=config.CACHE_SEMESTERS_EXPIRE_TIME)
            return semesters_data
    else:
        return error_code.WEBAP_ERROR

    return error_code.WEBAP_ERROR


def midterm_alerts(username, password, year, semester):
    """Retrun this semester midterm alerts list

    Args:
        username ([str]): NKUST webap username
        password ([str]): NKUST webap password
        year ([str]): 107  108 .. term year
        semester ([str]): semester

    Returns:
        [dict]: midterm alerts

        in any error
        [int]: CACHE_AP_QUERY_USERINFO_ERROR
               CACHE_WEBAP_LOGIN_FAIL
               CACHE_WEBAP_SERVER_ERROR
               CACHE_WEBAP_ERROR
               MIDTERM_ALERTS_ERROR
    """
    login_status = login(username=username, password=password)

    if login_status == error_code.CACHE_WENAP_LOGIN_SUCCESS:
        midterm_alerts_html = cache_ap_query(username=username,
                                             qid='ag009', arg01=year, arg02=semester)
        if midterm_alerts_html != False:
            if isinstance(midterm_alerts_html, str):
                res = parse.midterm_alert(midterm_alerts_html)
                return res
    else:
        return login_status
    return error_code.MIDTERM_ALERTS_ERROR


def cache_ap_query(username, qid,
                   expire_time=config.CACHE_WEBAP_QUERY_DEFAULT_EXPIRE_TIME,
                   **kwargs):
    """cache query 
    save html cache to redis 

    Args:
        username ([str]): use to get redis cache or set.
        qid ([str]): NKUST query url qrgs
        expire_time ([int]): Defaults to config.CACHE_WEBAP_QUERY_DEFAULT_EXPIRE_TIME.

        kwargs:
            (e.g.)
            cache_ap_query(username, qid='ag008',
                           yms='107,2', arg01='107', arg02='2')

            post data will = {
                'yms':'107,2',
                'arg01':'107',
                'arg02':'2'
            }

    Returns:
        [str]: html.
        [bool]: something erorr False.
    """
    if not red_bin.exists('webap_cookie_%s' % username):
        return error_code.CACHE_AP_QUERY_COOKIE_ERROR

    # webap_query_1105133333_ag008_107,2_...
    redis_name = "webap_query_{username}_{qid}".format(
        username=username, qid=qid)+'_'.join(map(str, kwargs.values()))
    # return cache (html)
    if red_string.exists(redis_name):
        return red_string.get(redis_name)

    # load redis cookie
    session = requests.session()
    session.cookies = pickle.loads(red_bin.get('webap_cookie_%s' % username))

    res = webap_crawler.query(session=session, qid=qid, **kwargs)

    if res != False:
        if res.status_code == 200:
            red_string.set(name=redis_name, value=res.text, ex=expire_time)

            return res.text
    return False
