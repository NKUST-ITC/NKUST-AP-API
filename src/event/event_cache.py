# coding=utf-8
# This file not only in cache layer or crawler layer, so...
#  create new dir to save this.
import pickle

import requests

from utils import config
from event import event_config
from event.event_error_code import error, coviddefenseError
import redis

red_bin = redis.StrictRedis.from_url(url=config.REDIS_URL, db=3)

login_url = 'https://coviddefense.nkust.edu.tw/accessControl/seatLogin/login'
token_login_url = 'https://coviddefense.nkust.edu.tw/accessControl/seatLogin/tokenLogin'
confirm_url = 'https://coviddefense.nkust.edu.tw/accessControl/seatLogin/loginSeat'


def info_parse(info_data: dict):

    result = {
        '_private_code': 0,
        'code': 0,
        'description': "成功",
        'title': '',
        "data": []
    }
    if "seat" not in info_data.keys():
        return error.something_error
    place_code = info_data['seat'].get("place_status", False)
    if place_code == "1" or place_code == "2":
        # student restaurant classroom seat
        if place_code == "1":
            result['_private_code'] = 1
            result['code'] = '學餐登入'
        elif place_code == "2":
            result['_private_code'] = 2
            result['code'] = '教室登入'

        result['code'] = 200
        result['_data'] = {}
        # check field
        require_field = ['group_name', 'place_name', 'column_row']

        name_string = ""
        for k, v in info_data['seat'].items():
            if k == 'column_row':
                _temp_column_row_name = v.split("-")
                if len(_temp_column_row_name) != 2:
                    _temp_column_row_name = [0, 0]
                name_string += "-{col}排{row}列".format(col=_temp_column_row_name[0],
                                                      row=_temp_column_row_name[1])
            elif k in require_field:
                name_string += v+"-"
        result['_data'].update({'name': name_string})

    elif info_data['seat'].get("place_status", False) == "4":
        # bus seat
        result['_private_code'] = 4
        result['code'] = 200
        result['title'] = '校車登入'
        if isinstance(info_data['bus_timetable_list'], list):
            if len(info_data['bus_timetable_list']) == 0:
                result['data'] = []
            # check field
            check_field = info_data['bus_timetable_list'][0].values()
            for i in ['id', 'start', 'end', 'name']:
                if i not in check_field:
                    result['data'] = []
                    break
            result['data'] = info_data['bus_timetable_list']
    else:
        return error.something_error
    return result


def coviddefense_login(session: requests.session,
                       account: str, password: str, seat_id: str, token=None):
    post_data = {"member": {"account": account,
                            "password": password,
                            "name": ""},
                 "seat": seat_id}
    post_url = login_url
    if token is not None:
        post_url = token_login_url
        post_data = {
            "member": {
                "account": "",
                "password": "",
                "name": ""
            },
            "seatKey": seat_id,
            "token": token
        }

    req = session.post(url=post_url, json=post_data)
    if req.status_code == 200:
        req = req.json()

        if req['status'] == "success":
            if token is None:
                session.cookies.update({"token": req['token']})
            return info_parse(req)
        elif req['status'] == 'error':
            if req['data'].find('密碼錯誤') > -1:
                return error.wrong_account_or_password
            if req['data'].find('查無此座位') > -1:
                return error.not_found_seat

    return error.something_error


def coviddefense_token_login(session: requests.session, seat_id: str):
    if not session.cookies.get('token'):
        # maybe token expire.
        return error.token_error
    return coviddefense_login(session=session, seat_id=seat_id, account='',
                              password='', token=session.cookies.get('token'))


def coviddefense_send_confirm(session, seat_id=None, bus_id=""):
    post_data = {
        "token": session.cookies.get('token'),
        "seatKey": seat_id,
        "bus_timetable_id": bus_id
    }
    req = session.post(url=confirm_url, json=post_data)
    if req.status_code == 200:
        req = req.json()
    else:
        return False
    if req['status'] == 'success':
        return True
    return False


def coviddefense_info_and_send(account: str, password: str,
                               seat_id: str, bus_id="", send_confirm=False):

    session = requests.session()

    if not red_bin.exists('coviddefense_cookie_%s' % account):
        # login and save cookie in redis.
        login_status = coviddefense_login(session=session,
                                          account=account,
                                          password=password, seat_id=seat_id)
    else:
        # load cookie from redis
        session.cookies = pickle.loads(
            red_bin.get('coviddefense_cookie_%s' % account))
        login_status = coviddefense_token_login(
            session=session, seat_id=seat_id)
        if login_status is error.token_error:
            login_status = coviddefense_login(session=session,
                                              account=account,
                                              password=password, seat_id=seat_id)

    if isinstance(login_status, coviddefenseError):
        return login_status

    red_bin.set('coviddefense_cookie_%s' %
                account, pickle.dumps(session.cookies), ex=event_config.CACHE_COVIDEFENSE_EXPIRE_TIME)

    if isinstance(login_status, dict):
        if login_status['_private_code'] not in [1, 2, 4]:
            return error.something_error
        if login_status['_private_code'] in [1, 2]:
            # login_status['_data'].update({'id': seat_id})
            login_status['data'] = [login_status['_data']]
            del login_status['_data']
        if login_status['_private_code'] == 4 and send_confirm is True and bus_id == "":
            login_status['code'] = 401
            del login_status['_private_code']
            return login_status

    del login_status['_private_code']

    if send_confirm:
        confirem_status = coviddefense_send_confirm(
            session=session, seat_id=seat_id, bus_id=bus_id)
        if confirem_status == True and bus_id != "":
            # bus
            for i in login_status['data']:
                if i['id'] == bus_id:
                    login_status['data'] = i
                    break
        else:
            login_status['data'] = login_status['data'][0]

    return login_status
