import datetime
import json
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


def bus_reservations_record(username):
    """User reservations record query, use config.CACHE_BUS_TIMETABLE_EXPIRE_TIME
    to expire data.
    Args:
        username ([str]): webap username
    Returns:
        [str]: result type is json.
        [int]: CACHE_BUS_COOKIE_ERROR(612)
               CACHE_BUS_USER_ERROR(613)
               BUS_TIMEOUT_ERROR(604)
               BUS_ERROR(605)
    """

    if not red_bin.exists('bus_cookie_%s' % username):
        return error_code.CACHE_BUS_COOKIE_ERROR

    redis_name = "bus_reservations_{username}".format(username=username)

    if red_string.exists(redis_name):
        return red_string.get(redis_name)

    session = requests.session()
    session.cookies = pickle.loads(red_bin.get('bus_cookie_%s' % username))
    result = bus_crawler.reserve(
        session=session)

    if isinstance(result, list):
        return_data = {
            "data": result
        }
        json_dumps_data = json.dumps(return_data, ensure_ascii=False)
        red_string.set(
            name=redis_name,
            value=json_dumps_data,
            ex=config.CACHE_BUS_USER_RESERVATIONS)
        return json_dumps_data

    elif result == error_code.BUS_USER_WRONG_CAMPUS_OR_NOT_FOUND_USER:
        # clear user cache cookie
        red_bin.delete('bus_cookie_%s' % username)
        return error_code.CACHE_BUS_USER_ERROR
    # return error code
    return result


def bus_reserve_book(username, kid, action):
    """User reservations record query, use config.CACHE_BUS_TIMETABLE_EXPIRE_TIME
    to expire data.
    Args:
        username ([str]): webap username
    Returns:
        [dict]: result type is json.
        [int]: CACHE_BUS_COOKIE_ERROR(612)
               CACHE_BUS_USER_ERROR(613)
               BUS_TIMEOUT_ERROR(604)
               BUS_ERROR(605)
    """

    if not red_bin.exists('bus_cookie_%s' % username):
        return error_code.CACHE_BUS_COOKIE_ERROR

    session = requests.session()
    session.cookies = pickle.loads(red_bin.get('bus_cookie_%s' % username))
    result = bus_crawler.book(session=session, kid=kid, action=action)

    if isinstance(result, dict):
        if result['success']:
            # clear all bus cache, because data changed.
            for key in red_string.scan_iter('bus_*_{username}*'.format(username=username)):
                red_string.delete(key)
            return result
        else:
            return result

    elif result == error_code.BUS_USER_WRONG_CAMPUS_OR_NOT_FOUND_USER:
        # clear user cache cookie
        red_bin.delete('bus_cookie_%s' % username)
        return error_code.CACHE_BUS_USER_ERROR
    # return error code
    return result
