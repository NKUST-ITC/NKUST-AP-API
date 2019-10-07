import time
import json
import pickle

import redis
import requests

from crawler import leave_crawler
from utils import config, error_code

red_string = redis.StrictRedis.from_url(
    url=config.REDIS_URL, db=4, charset="utf-8", decode_responses=True)
red_bin = redis.StrictRedis.from_url(url=config.REDIS_URL, db=3)


def login(username, password):
    """ login leave system.

    Args:
        username ([str]): webap username
        password ([str]): webap password

    Returns:
        [int]: LEAVE_LOGIN_TIMEOUT(801)
               LEAVE_LOGIN_FAIL (803)
               CACHE_LEAVE_LOGIN_SUCCESS (804)
               CACHE_LEAVE_ERROR (805)
    """
    # check leave cookie exist
    if red_bin.exists('leave_cookie_%s' % username):
        return error_code.CACHE_LEAVE_LOGIN_SUCCESS

    session = requests.session()

    login_status = leave_crawler.login(
        session=session, username=username, password=password)

    if isinstance(login_status, int):
        if login_status == error_code.LEAVE_LOGIN_SUCCESS:
            red_bin.set(name='leave_cookie_%s' %
                        username, value=pickle.dumps(session.cookies), ex=config.CACHE_LEAVE_COOKIE_EXPIRE_TIME)

            return error_code.CACHE_LEAVE_LOGIN_SUCCESS
        else:
            return login_status

    return error_code.CACHE_LEAVE_ERROR


def get_leave_list(username, year, semester):
    """leave list

    Args:
        username ([str]): NKUST webap username
        year ([str]): 107  108 .. term year
        semester ([str]): semester

    Returns:
        [str]: result type is json.

        [int]:CACHE_LEAVE_ERROR
    """
    redis_name = "leave_list_{username}_{year}_{semester}".format(
        username=username,
        year=year,
        semester=semester)

    if red_string.exists(redis_name):
        return red_string.get(redis_name)

    session = requests.session()
    session.cookies = pickle.loads(red_bin.get('leave_cookie_%s' % username))

    list_data = leave_crawler.get_leave_list(
        session=session, year=year, semester=semester)
    if isinstance(list_data, list) and len(list_data) == 2:
        return_data = {
            "data": list_data[0],
            "timeCodes": list_data[1]
        }
        json_dumps_data = json.dumps(return_data, ensure_ascii=False)
        red_string.set(
            name=redis_name,
            value=json_dumps_data,
            ex=config.CACHE_LEAVE_LIST_EXPIRE_TIME)
        return json_dumps_data

    return error_code.CACHE_LEAVE_ERROR


def get_submit_info(username):
    """get submit info

    Args:
        username ([str]): NKUST webap username

    Returns:
        [str]: result type is json.

        [int]:CACHE_LEAVE_ERROR
    """
    redis_name = "leave_list_{username}_submit_info".format(
        username=username)

    if red_string.exists(redis_name):
        return red_string.get(redis_name)

    session = requests.session()
    session.cookies = pickle.loads(red_bin.get('leave_cookie_%s' % username))

    data = leave_crawler.get_submit_info(
        session=session)

    if isinstance(data, dict):

        json_dumps_data = json.dumps(data, ensure_ascii=False)
        red_string.set(
            name=redis_name,
            value=json_dumps_data,
            ex=config.CACHE_LEAVE_SUBMIT_EXPIRE_TIME)
        return json_dumps_data
    elif isinstance(data, int):
        if data == error_code.LEAVE_SUBMIT_INFO_GRADUATE_ERROR:
            return error_code.LEAVE_SUBMIT_INFO_GRADUATE_ERROR

    return error_code.CACHE_LEAVE_ERROR


def submit_leave(username, leave_data, leave_proof):
    """leave submit!

    Args:
        username ([str]): NKUST webap username
        leave_data ([dict]): leave detail 
        leave_proof ([streaming_form_data.targets.ValueTarget]):  image file.

    Returns:
        [bool]: True //success 
        [int]: 
        LEAVE_SUBMIT_WRONG_DATE = 810
        LEAVE_SUBMIT_SOMETHING_ERROR = 811
        LEAVE_SUBMIT_DATE_CONFLICT = 813
        LEAVE_SUBMIT_ERROR = 814
    """

    session = requests.session()
    session.cookies = pickle.loads(red_bin.get('leave_cookie_%s' % username))
    # --format input data--
    leave_data['days'] = sorted(leave_data['days'], key=lambda k: k['day'])
    # convert class to index numbe
    class_map = {"A": 5, "M": 0}
    for day in leave_data['days']:
        _temp_list = []
        for class_data in day['class']:
            if class_map.get(class_data, False):
                class_data = class_map.get(class_data, False)
            else:
                class_data = int(class_data)+1
            _temp_list.append(class_data)
        day['class'] = _temp_list
    for day in leave_data['days']:
        _temp_day_format = time.strptime(day['day'], '%Y/%m/%d')
        day['day'] = "{term_year}/{month}/{day}".format(term_year=_temp_day_format.tm_year - 1911,
                                                        month=_temp_day_format.tm_mon,
                                                        day=_temp_day_format.tm_mday)

    image_type = 'jpeg'
    if leave_proof != None:
        if leave_proof.multipart_filename[-3:] not in ['png', 'PNG']:
            image_type = 'png'

    data = leave_crawler.leave_submit(
        session=session,
        leave_data=leave_data,
        proof_file=leave_proof.value,
        proof_file_name=leave_proof.multipart_filename,
        proof_type=image_type)

    if isinstance(data, int):
        if data == error_code.LEAVE_SUBMIT_SUCCESS:
            return True
        # other int in view to check.
        return data

    return error_code.LEAVE_SUBMIT_ERROR
