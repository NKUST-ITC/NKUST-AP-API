import hashlib
import pickle

import redis
import requests

from crawler import webap_crawler
from utils import error_code
from utils import config
from utils.config import REDIS_URL

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

    # without check ssl verify
    session.verify = False
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
                    username, value=pickle.dumps(session.cookies))

        return error_code.CACHE_WENAP_LOGIN_SUCCESS

    elif login_status == error_code.WEBAP_LOGIN_FAIL:
        return error_code.CACHE_WEBAP_LOGIN_FAIL
    elif login_status == error_code.WEBAP_SERVER_ERROR:
        return error_code.CACHE_WEBAP_SERVER_ERROR
    elif login_status == error_code.WEBAP_ERROR:
        return error_code.CACHE_WEBAP_ERROR

    return error_code.CACHE_WEBAP_ERROR
