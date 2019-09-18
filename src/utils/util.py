import random
import string

import falcon

from cache.ap_cache import login as webap_login
from cache.bus_cache import login as bus_login
from cache.leave_cache import login as leave_login
from utils import error_code, config


def randStr(lens):
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(lens)])


def max_body(limit):
    def hook(req, resp, resource, params):
        length = req.content_length
        if length is not None and length > limit:
            msg = ('The size of the request is too large. The body must not '
                   'exceed ' + str(limit) + ' bytes in length.')

            raise falcon.HTTPPayloadTooLarge(
                'Request body is too large', msg)

    return hook


def webap_login_cache_required(req, resp, resource, params):
    """This function is for falcon.before to use, like a decorator,
    check user have cache cookie.

    Args:
        req ([type]): falcon default.
        resp ([type]): falcon default.
        resource ([type]): falcon default.
        params ([type]): falcon default.

    Raises:
        falcon.HTTPUnauthorized: HTTP_401,Just login fail,or maybe NKUST server is down.
        falcon.HTTPServiceUnavailable: HTTP_503, NKUST server problem.
        falcon.HTTPInternalServerError: HTTP_500, something error.

    Returns:
        [bool]: True, login success.
    """
    # jwt payload
    payload = req.context['user']['user']
    login_status = webap_login(
        username=payload['username'], password=payload['password'])

    if login_status == error_code.CACHE_WENAP_LOGIN_SUCCESS:
        return True
    elif login_status == error_code.CACHE_WEBAP_LOGIN_FAIL:
        raise falcon.HTTPUnauthorized(description='login fail')
    elif login_status == error_code.CACHE_WEBAP_SERVER_ERROR:
        raise falcon.HTTPServiceUnavailable()
    elif login_status == error_code.CACHE_WEBAP_ERROR:
        raise falcon.HTTPInternalServerError()
    raise falcon.HTTPInternalServerError()


def bus_login_cache_required(req, resp, resource, params):
    """This function is for falcon.before to use, like a decorator,
    check user have cache cookie.

    Args:
        req ([type]): falcon default.
        resp ([type]): falcon default.
        resource ([type]): falcon default.
        params ([type]): falcon default.

    Raises:
        falcon.HTTPUnauthorized: HTTP_401, login fail,or maybe NKUST server is down.
        falcon.HTTPForbidden: HTTP_403, wrong campus.
        falcon.HTTPServiceUnavailable: HTTP_503, NKUST server problem, timeout.
        falcon.HTTPInternalServerError: HTTP_500, something error.

    Returns:
        [bool]: True, login success.
    """
    # jwt payload
    payload = req.context['user']['user']
    login_status = bus_login(
        username=payload['username'], password=payload['password'])

    if login_status == error_code.CACHE_BUS_LOGIN_SUCCESS:
        return True
    elif login_status == error_code.BUS_WRONG_PASSWORD:
        # 401
        raise falcon.HTTPUnauthorized(description='login fail')
    elif login_status == error_code.BUS_USER_WRONG_CAMPUS_OR_NOT_FOUND_USER:
        # 403
        raise falcon.HTTPForbidden(description='wrong campus')
    elif login_status == error_code.BUS_TIMEOUT_ERROR:
        # 503
        raise falcon.HTTPServiceUnavailable()
    raise falcon.HTTPInternalServerError()


def leave_login_cache_required(req, resp, resource, params):
    """This function is for falcon.before to use, like a decorator,
    check user have cache cookie.

    Args:
        req ([type]): falcon default.
        resp ([type]): falcon default.
        resource ([type]): falcon default.
        params ([type]): falcon default.

    Raises:
        falcon.HTTPUnauthorized: HTTP_401, login fail,or maybe NKUST server is down.
        falcon.HTTPServiceUnavailable: HTTP_503, NKUST server problem, timeout.
        falcon.HTTPInternalServerError: HTTP_500, something error.

    Returns:
        [bool]: True, login success.
    """
    # jwt payload
    payload = req.context['user']['user']
    login_status = leave_login(
        username=payload['username'], password=payload['password'])

    if login_status == error_code.CACHE_LEAVE_LOGIN_SUCCESS:
        return True
    elif login_status == error_code.LEAVE_LOGIN_FAIL:
        # 401
        raise falcon.HTTPUnauthorized(description='login fail')
    elif login_status == error_code.LEAVE_LOGIN_TIMEOUT:
        # 503
        raise falcon.HTTPServiceUnavailable()
    raise falcon.HTTPInternalServerError()


def falcon_admin_required(req, resp, resource, params):
    """This function is for falcon.before to use, like a decorator,
    check user status, for news use.

    Args:
        req ([type]): falcon default.
        resp ([type]): falcon default.
        resource ([type]): falcon default.
        params ([type]): falcon default.

    Raises:
        falcon.HTTPUnauthorized: HTTP_401, login fail,or maybe NKUST server is down.
        falcon.HTTPInternalServerError: HTTP_500, something error.

    Returns:
        [bool]: True.
    """
    # jwt payload
    payload = req.context['user']['user']

    if payload['username'] in config.NEWS_ADMIN:
        return True
    else:
        # 401
        raise falcon.HTTPUnauthorized(description='not a admin :( ')
    raise falcon.HTTPInternalServerError()
