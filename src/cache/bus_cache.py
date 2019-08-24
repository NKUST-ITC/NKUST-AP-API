import pickle

import redis
import requests

from crawler import bus_crawler
from utils import config, error_code

red_string = redis.StrictRedis.from_url(
    url=config.REDIS_URL, db=4, charset="utf-8", decode_responses=True)
red_bin = redis.StrictRedis.from_url(url=config.REDIS_URL, db=3)


def login(username, password):
    """ login bus system.

    Args:
        username ([str]): webap username
        password ([str]): webap password

    Returns:
        [int]: BUS_JS_ERROR(601)
               BUS_USER_WRONG_CAMPUS_OR_NOT_FOUND_USER(602)
               BUS_WRONG_PASSWORD(603)
               BUS_TIMEOUT_ERROR(604)
               BUS_ERROR(605)
               CACHE_BUS_LOGIN_SUCCESS(610)
               CACHE_BUS_ERROR(611)

    """
    # check webap cookie exist
    if red_bin.exists('bus_cookie_%s' % username):
        return error_code.CACHE_BUS_LOGIN_SUCCESS

    session = requests.session()

    login_status = bus_crawler.login(
        session=session, username=username, password=password)

    if isinstance(login_status, dict):
        # save cookie to redis
        red_bin.set(name='bus_cookie_%s' %
                    username, value=pickle.dumps(session.cookies), ex=config.CACHE_BUS_COOKIE_EXPIRE_TIME)

        return error_code.CACHE_BUS_LOGIN_SUCCESS
    elif isinstance(login_status, int):
        return login_status

    return error_code.CACHE_BUS_ERROR
