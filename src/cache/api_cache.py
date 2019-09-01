import datetime
import json
import subprocess
from multiprocessing.pool import ThreadPool

import redis
import requests

from crawler import bus_crawler, webap_crawler
from utils import config, error_code
from utils.config import REDIS_URL

red_string = redis.StrictRedis.from_url(
    url=REDIS_URL, db=4, charset="utf-8", decode_responses=True)

WRONG_ACCOUNT = 'abcdefg'
WRONG_PASSWORD = 'wowisatest'

LEAVE_URL = 'http://leave.nkust.edu.tw/LogOn.aspx'
LIBRARY_URL = 'http://www.lib.nkust.edu.tw/portal/portal_login.php'


def _request(session, url, timeout):
    try:
        if session.get(url=url, timeout=timeout).status_code == 200:
            return 100
    except requests.exceptions.ConnectTimeout as e:
        return 101
    return 101


def server_status():

    if red_string.exists('server_status'):
        return red_string.get('server_status')

    req_session = requests.session()
    pool = ThreadPool(processes=4)

    bus_test = pool.apply_async(bus_crawler.login, kwds={
        'session': req_session,
        'username': WRONG_ACCOUNT,
        'password': WRONG_PASSWORD
    })
    webap_test = pool.apply_async(webap_crawler.login, kwds={
        'session': req_session,
        'username': config.AP_GUEST_ACCOUNT,
        'password': config.AP_GUEST_PASSWORD
    })

    leave_test = pool.apply_async(_request, kwds={
        'session': req_session,
        'url': LEAVE_URL,
        'timeout': 4
    })
    library_test = pool.apply_async(_request, kwds={
        'session': req_session,
        'url': LIBRARY_URL,
        'timeout': 4
    })

    git_commit_id = subprocess.check_output(
        ['git', 'rev-parse', '--short', 'HEAD']).decode("utf-8").strip("\n")

    data = {
        "date": datetime.datetime.now().isoformat(),
        "commit": git_commit_id,
        "data": [
            {
                "service": "ap",
                "isAlive": webap_test.get() is error_code.WENAP_LOGIN_SUCCESS,
                "description": "校務系統"
            },
            {
                "service": "bus",
                "isAlive": bus_test.get() is error_code.BUS_USER_WRONG_CAMPUS_OR_NOT_FOUND_USER,
                "description": "校車系統"
            },
            {
                "service": "leave",
                "isAlive": leave_test.get() is 100,
                "description": "缺曠系統"
            },
            {
                "service": "library",
                "isAlive": library_test.get()is 100,
                "description": "圖書館系統"
            }
        ]
    }
    _dumps = json.dumps(data, ensure_ascii=False)
    red_string.set(name='server_status', value=_dumps,
                   ex=config.CACHE_SERVER_STATUS_EXPITE_TIME)

    return _dumps
