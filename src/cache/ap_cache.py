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


def user_info(username):
    """After use webap_login_cache_required.
    Get user info.

    Args:
        username ([str]): NKUST webap username

    Returns:
        [dict]: user info

        in any error
        [int]: CACHE_AP_QUERY_USERINFO_ERROR
               USER_INFO_PARSE_ERROR
               USER_INFO_ERROR
    """
    # check login

    res = cache_ap_query(username=username, qid='ag003')
    if res == False:
        return error_code.CACHE_AP_QUERY_USERINFO_ERROR
    user_info_parse = parse.userinfo(html=res)
    if user_info_parse == False:
        return error_code.USER_INFO_PARSE_ERROR
    else:
        return user_info_parse

    return error_code.USER_INFO_ERROR


def graduate_user_info(username):
    """Get graduate name from webap header.
    save string data in redis 

    Args:
        username ([str]): [description]

    Returns:
        [str]: result type is json

        error
        [int]: CACHE_AP_QUERY_COOKIE_ERROR
               USER_INFO_ERROR

    """
    if not red_bin.exists('webap_cookie_%s' % username):
        return error_code.CACHE_AP_QUERY_COOKIE_ERROR

    redis_name = "graduate_user_info_{username}".format(
        username=username)

    if red_string.exists(redis_name):
        return red_string.get(redis_name)

    # load redis cookie
    session = requests.session()
    session.cookies = pickle.loads(red_bin.get('webap_cookie_%s' % username))
    html = webap_crawler.graduate_user_info(session=session)
    if html is not False:
        if isinstance(html.text, str):
            res = parse.graduate_user_info(html=html.text)
            if isinstance(res, dict):
                res['id'] = username
                _res_dumps = json.dumps(res, ensure_ascii=False)
                red_string.set(
                    name=redis_name,
                    value=_res_dumps,
                    ex=config.CACHE_GRADUATE_USER_INFO_EXPIRE_TIME)
                return _res_dumps
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
                CACHE_WEBAP_LOGIN_FAIL (111)
                CACHE_WEBAP_SERVER_ERROR (112)
                CACHE_WEBAP_ERROR (113)

    """
    if red_string.exists('semesters'):
        return red_string.get('semesters')

    login_status = login(username=config.AP_GUEST_ACCOUNT,
                         password=config.AP_GUEST_PASSWORD)

    if login_status == error_code.CACHE_WENAP_LOGIN_SUCCESS:
        session = requests.session()
        # load guest cookie
        session.cookies = pickle.loads(red_bin.get(
            'webap_cookie_%s' % config.AP_GUEST_ACCOUNT))
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
        return error_code.CACHE_WEBAP_ERROR

    return error_code.CACHE_WEBAP_ERROR


def midterm_alerts(username, year, semester):
    """After use webap_login_cache_required.
    Retrun this semester midterm alerts list.

    Args:
        username ([str]): NKUST webap username
        year ([str]): 107  108 .. term year
        semester ([str]): semester

    Returns:
        [dict]: midterm alerts

        in any error
        [int]: CACHE_AP_QUERY_USERINFO_ERROR
               MIDTERM_ALERTS_ERROR
               MIDTERM_ALERTS_PARSER_ERROR
    """

    midterm_alerts_html = cache_ap_query(username=username,
                                         qid='ag009', arg01=year, arg02=semester)
    if midterm_alerts_html != False:
        if isinstance(midterm_alerts_html, str):
            res = parse.midterm_alert(midterm_alerts_html)
            if res is False:
                return error_code.MIDTERM_ALERTS_PARSER_ERROR
            return res
        else:
            return error_code.CACHE_AP_QUERY_USERINFO_ERROR

    return error_code.MIDTERM_ALERTS_ERROR


def score(username, year, semester):
    """After use webap_login_cache_required.
    Retrun this semester score.

    Args:
        username ([str]): NKUST webap username
        year ([str]): 107  108 .. term year
        semester ([str]): semester

    Returns:
        [dict]: score

        in any error
        [int]:  SCORES_PARSE_ERROR
                SCORES_ERROR
    """

    scores_html = cache_ap_query(username=username,
                                 qid='ag008', arg01=year, arg02=semester)
    if scores_html is not False:
        if isinstance(scores_html, str):
            res = parse.scores(scores_html)
            if res is False:
                # 204
                return error_code.SCORES_PARSE_ERROR
            return res

    return error_code.SCORES_ERROR


def coursetable(username, year, semester):
    """After use webap_login_cache_required.
    Retrun course table.

    This function not save html in redis, is json(str).
    Because parse course table is too ...( ;u; )

    Args:
        username ([str]): NKUST webap username
        year ([str]): 107  108 .. term year
        semester ([str]): semester

    Returns:
        [str]: coursetable_data, json (str)

        in any error
        [int]: COURSETABLE_PARSE_ERROR
               COURSETABLE_QUERY_ERROR
               WEBAP_ERROR
    """

    if red_string.exists('coursetable_%s_%s_%s' % (username, year, semester)):
        return red_string.get('coursetable_%s_%s_%s' % (username, year, semester))

    session = requests.session()
    # load webap cookie
    session.cookies = pickle.loads(
        red_bin.get('webap_cookie_%s' % username))
    query_res = webap_crawler.query(
        session=session, qid='ag222', arg01=year, arg02=semester)

    if not query_res:
        return error_code.COURSETABLE_QUERY_ERROR

    elif isinstance(query_res, requests.models.Response):
        res = parse.coursetable(query_res.text)
        if res is False:
            return error_code.COURSETABLE_PARSE_ERROR

        coursetable_data = json.dumps(res)
        red_string.set(name='coursetable_%s_%s_%s' % (username, year, semester),
                       value=coursetable_data,
                       ex=config.CACHE_COURSETABLE_EXPIRE_TIME)
        return coursetable_data

    return error_code.WEBAP_ERROR


def reward(username, year, semester):
    """After use webap_login_cache_required.
    Retrun this semester reward.

    Args:
        username ([str]): NKUST webap username
        year ([str]): 107  108 .. term year
        semester ([str]): semester

    Returns:
        [dict]: reward dict

        in any error
        [int]: REWARD_ERROR
               REWARD_PARSE_ERROR
    """

    scores_html = cache_ap_query(username=username,
                                 qid='ak010', arg01=year, arg02=semester)
    if scores_html:
        if isinstance(scores_html, str):
            res = parse.reward(scores_html)
            if res is False:
                return error_code.REWARD_PARSE_ERROR
            return res

    return error_code.REWARD_ERROR


def cache_graduation_threshold(username, password):
    """Retrun  graduation threshold.
    **NKUST maybe abandon this function**

    Args:
        username ([str]): NKUST webap username
        password ([str]): NKUST webap password

    Returns:
        [str]: json(str)

        in any error
        [int]: CACHE_WEBAP_LOGIN_FAIL
               CACHE_WEBAP_SERVER_ERROR
               CACHE_WEBAP_ERROR
               GRADUATION_ERROR
    """
    # graduation_username
    if red_string.exists('graduation_%s' % username):
        return red_string.get(('graduation_%s' % username))

    login_status = login(username=username, password=password)
    if login_status == error_code.CACHE_WENAP_LOGIN_SUCCESS:

        # load user cookie
        session = requests.session()
        session.cookies = pickle.loads(
            red_bin.get('webap_cookie_%s' % username))

        graduation_req = webap_crawler.graduation_threshold(session=session)

        if graduation_req != False:
            if isinstance(graduation_req.text, str):
                res = parse.graduation(graduation_req.text)
                if res != False:
                    dump = json.dumps(res, ensure_ascii=False)
                    red_string.set(name='graduation_%s' % username,
                                   value=dump, ex=config.CACHE_GRADUTION_EXPIRE_TIME)

                    return dump
    else:
        return login_status
    return error_code.GRADUATION_ERROR


def room_list(campus):
    """/user/room/list
    campus
    1=建工/2=燕巢/3=第一/4=楠梓/5=旗津
    get campus room list 
    In this function, without use cache_ap_query
    use webap_crawler.query and use GUEST account.

    Returns:
        [str]: result type is json

        error:
            [int]
                ROOM_LIST_ERROR
                CACHE_WEBAP_LOGIN_FAIL (111)
                CACHE_WEBAP_SERVER_ERROR (112)
                CACHE_WEBAP_ERROR (113)

    """
    if red_string.exists('campus_%s' % campus):
        return red_string.get('campus_%s' % campus)

    login_status = login(username=config.AP_GUEST_ACCOUNT,
                         password=config.AP_GUEST_PASSWORD)

    if login_status == error_code.CACHE_WENAP_LOGIN_SUCCESS:
        session = requests.session()
        # load guest cookie
        session.cookies = pickle.loads(red_bin.get(
            'webap_cookie_%s' % config.AP_GUEST_ACCOUNT))
        query_res = webap_crawler.query(
            session=session, qid='ag302_01', cmp_area_id=campus)
        if query_res == False:
            return error_code.ROOM_LIST_ERROR

        elif isinstance(query_res, requests.models.Response):
            room_list_data = json.dumps(parse.room_list(query_res.text))
            red_string.set(name='campus_%s' % campus,
                           value=room_list_data,
                           ex=config.CACHE_SEMESTERS_EXPIRE_TIME)
            return room_list_data
    else:
        return error_code.CACHE_WEBAP_ERROR

    return error_code.CACHE_WEBAP_ERROR


def query_empty_room(room_id, year, semester):
    """/user/empty-room/info
    Query the room course table

    In this function, without use cache_ap_query
    use webap_crawler.query and use GUEST account.

    Args:
        room_id ([str]): After get from room_list
        year ([str]): 107  108.
        semester ([str]): semester 1,2...

    Returns:
        [str]: result type is json


    """

    cache_redis_name = "room_coursetable_{room_id}_{year}_{semester}".format(
        room_id=room_id,
        year=year,
        semester=semester
    )

    if red_string.exists(cache_redis_name):
        return red_string.get(cache_redis_name)

    login_status = login(username=config.AP_GUEST_ACCOUNT,
                         password=config.AP_GUEST_PASSWORD)

    if login_status == error_code.CACHE_WENAP_LOGIN_SUCCESS:
        session = requests.session()

        # load guest cookie
        session.cookies = pickle.loads(red_bin.get(
            'webap_cookie_%s' % config.AP_GUEST_ACCOUNT))

        yms_data = "{year}#{semester}".format(year=year, semester=semester)
        query_res = webap_crawler.query(
            session=session, qid='ag302_02', room_id=room_id, yms_yms=yms_data)

        if query_res == False:
            return error_code.QUERY_EMPTY_ROOM_ERROR

        elif isinstance(query_res, requests.models.Response):
            room_coursetable_data = json.dumps(
                parse.query_room(query_res.text))

            if len(room_coursetable_data) < 160:
                # avoid null data save in redis.
                return error_code.CACHE_WEBAP_ERROR

            red_string.set(name=cache_redis_name,
                           value=room_coursetable_data,
                           ex=config.CACHE_SEMESTERS_EXPIRE_TIME)
            return room_coursetable_data
    else:
        return error_code.CACHE_WEBAP_ERROR

    return error_code.CACHE_WEBAP_ERROR


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
