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
