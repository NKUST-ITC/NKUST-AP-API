import json
import pickle
from datetime import datetime, timedelta
from multiprocessing.pool import ThreadPool

import redis
import requests

from crawler import bus_crawler
from utils import config, error_code

red_string = redis.StrictRedis.from_url(
    url=config.REDIS_URL, db=4, charset="utf-8", decode_responses=True)
red_bin = redis.StrictRedis.from_url(url=config.REDIS_URL, db=3)
pool = ThreadPool()


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


def bus_query(username, year, month, day):
    """bus timetable query, use config.CACHE_BUS_TIMETABLE_EXPIRE_TIME
    to expire data.


    Args:
        username ([str]): webap username
        year ([int]): year, common era.
        month ([int]): month.
        day ([int]): day.

    Returns:
        [str]: result type is json.

        [int]: CACHE_BUS_COOKIE_ERROR(612)
               CACHE_BUS_USER_ERROR(613)
               BUS_TIMEOUT_ERROR(604)
               BUS_ERROR(605)
    """

    if not red_bin.exists('bus_cookie_%s' % username):
        return error_code.CACHE_BUS_COOKIE_ERROR

    redis_name = "bus_timetable_{username}_{year}_{month}_{day}".format(
        username=username,
        year=year,
        month=month,
        day=day)

    if red_string.exists(redis_name):
        return red_string.get(redis_name)

    session = requests.session()
    session.cookies = pickle.loads(red_bin.get('bus_cookie_%s' % username))
    pool = ThreadPool(processes=1)
    async_result = pool.apply_async(bus_reservations_record, (username,))

    result = bus_crawler.query(
        session=session, year=year, month=month, day=day)

    if isinstance(result, list):

        if not isinstance(async_result.get(), str):
            return error_code.BUS_ERROR
        # mix cancelKey in timetable
        user_reservation = json.loads(async_result.get())
        for bus_data in result:
            bus_data['cancelKey'] = ''
            if bus_data['isReserve']:
                for reservation_data in user_reservation['data']:
                    if reservation_data['dateTime'] == bus_data['departureTime']:
                        bus_data['cancelKey'] = reservation_data['cancelKey']

        return_data = {
            "date": datetime.datetime.utcnow().isoformat(timespec='seconds')+"Z",
            "data": result
        }
        json_dumps_data = json.dumps(return_data, ensure_ascii=False)
        red_string.set(
            name=redis_name,
            value=json_dumps_data,
            ex=config.CACHE_BUS_TIMETABLE_EXPIRE_TIME)
        return json_dumps_data

    elif result == error_code.BUS_USER_WRONG_CAMPUS_OR_NOT_FOUND_USER:
        # clear user cache cookie
        red_bin.delete('bus_cookie_%s' % username)
        return error_code.CACHE_BUS_USER_ERROR
    # return error code
    return result


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


def bus_violation(username):
    """bus timetable query, use config.CACHE_BUS_TIMETABLE_EXPIRE_TIME
    to expire data.
    Args:
        username ([str]): webap username
    Returns:
        [str]: result type is json.
        [int]: CACHE_BUS_COOKIE_ERROR(612)
               BUS_TIMEOUT_ERROR(604)
               BUS_ERROR(605)
    """

    if not red_bin.exists('bus_cookie_%s' % username):
        return error_code.CACHE_BUS_COOKIE_ERROR

    redis_name = "bus_violation-records_{username}".format(
        username=username)

    if red_string.exists(redis_name):
        return red_string.get(redis_name)

    session = requests.session()
    session.cookies = pickle.loads(red_bin.get('bus_cookie_%s' % username))
    result = bus_crawler.get_violation_records(session=session)

    if isinstance(result, list):
        return_data = {
            "reservation": result
        }
        json_dumps_data = json.dumps(return_data, ensure_ascii=False)
        red_string.set(
            name=redis_name,
            value=json_dumps_data,
            ex=config.CACHE_BUS_VIOLATION_RECORD_EXPIRE_TIME)
        return json_dumps_data

    # return error code
    return result


def get_and_update_timetable_cache(session: requests.session, year: int, month: int, day: int):
    "Just update redis bus timetable"
    redis_name = "bus_timetable_{year}_{month}_{day}".format(
        year=year,
        month=month,
        day=day)

    main_timetable = bus_crawler.query(
        session=session, year=year, month=month, day=day)

    if isinstance(main_timetable, list):
        red_string.set(
            name=redis_name,
            value=json.dumps(main_timetable, ensure_ascii=False),
            ex=config.CACHE_BUS_TIMETABLE_EXPIRE_TIME)
        if isinstance(main_timetable, list) and len(main_timetable) > 0:
            expire_seconds = ((datetime.strptime(
                main_timetable[0]['departureTime'], "%Y-%m-%dT%H:%M:%SZ")
                + timedelta(days=1))-datetime.now()).total_seconds()

            if expire_seconds > 0:
                red_string.set(
                    name=redis_name,
                    value=json.dumps(main_timetable, ensure_ascii=False),
                    ex=round(expire_seconds))
        return main_timetable
