import json
import pickle

import redis
import requests

from crawler import library_crawler
from utils import config, error_code

red_string = redis.StrictRedis.from_url(
    url=config.REDIS_URL, db=4, charset="utf-8", decode_responses=True)
red_bin = redis.StrictRedis.from_url(url=config.REDIS_URL, db=3)


def login(username, password):
    """ login library system.

    Args:
        username ([str]): webap username
        password ([str]): webap password

    Returns:
        [int]: LIBRARY_LOGIN_SUCCESS(710)
               LIBRARY_LOGIN_FAIL(712)
               LIBRARY_ERROR(713)
               CACHE_LIBRARY_ERROR(714)
               CACHE_LIBRARY_LOGIN_SUCCESS(715)

    """
    # check webap cookie exist
    if red_bin.exists('library_cookie_%s' % username):
        return error_code.CACHE_LIBRARY_LOGIN_SUCCESS

    session = requests.session()

    login_status = library_crawler.login(
        session=session, username=username, password=password)

    if isinstance(login_status, int):
        # save cookie to redis
        if login_status == error_code.LIBRARY_LOGIN_SUCCESS:
            red_bin.set(name='library_cookie_%s' %
                        username, value=pickle.dumps(session.cookies), ex=config.CACHE_LIBRARY_EXPIRE_TIME)
            return error_code.CACHE_LIBRARY_LOGIN_SUCCESS
        return login_status

    return error_code.CACHE_LIBRARY_ERROR


def userinfo(username):
    """library user info.

    Args:
        username ([str]): username of NKUST ap system, actually your NKUST student id.

    Returns:
        [str]: json (str)

        [int]: CACHE_LIBRARY_ERROR
               LIBRARY_ERROR
    """
    if not red_bin.exists('library_cookie_%s' % username):
        return error_code.CACHE_LIBRARY_ERROR

    redis_name = "library_user_info_{username}".format(
        username=username)

    if red_string.exists(redis_name):
        return red_string.get(redis_name)

    # load redis cookie
    session = requests.session()
    session.cookies = pickle.loads(red_bin.get('library_cookie_%s' % username))
    user_info = library_crawler.user_info(session=session)
    if isinstance(user_info, dict):
        _res_dumps = json.dumps(user_info, ensure_ascii=False)
        red_string.set(
            name=redis_name,
            value=_res_dumps,
            ex=config.CACHE_LIBRARY_USER_INFO_EXPIRE_TIME)
        return _res_dumps
    return error_code.LIBRARY_ERROR
