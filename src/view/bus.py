import re

import falcon

from cache import bus_cache
from utils import error_code
from utils.util import bus_login_cache_required


class busUserReservations:

    @falcon.before(bus_login_cache_required)
    def on_get(self, req, resp):

        payload = req.context['user']['user']
        reslut = bus_cache.bus_reservations_record(
            username=payload['username'])

        if isinstance(reslut, str):
            resp.body = reslut
            resp.media = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
            return True
        # error handle
        elif isinstance(reslut, int):
            if reslut == error_code.CACHE_BUS_COOKIE_ERROR:
                raise falcon.HTTPInternalServerError(
                    description='api server not found cookie.')
            elif reslut == error_code.CACHE_BUS_USER_ERROR:
                raise falcon.HTTPForbidden(
                    description='NKUST server not found user data.')
            elif reslut == error_code.BUS_TIMEOUT_ERROR:
                raise falcon.HTTPServiceUnavailable(description='timeout')

        raise falcon.HTTPInternalServerError(
            description='something error ?')

    @falcon.before(bus_login_cache_required)
    def on_put(self, req, resp):
        payload = req.context['user']['user']
        if req.get_param('busId') == None or req.get_param('busId') == '':
            raise falcon.HTTPBadRequest(description='params error')

        result = bus_cache.bus_reserve_book(
            username=payload['username'], kid=req.get_param('busId'), action=True)

        if isinstance(result, dict):
            resp.media = result
            resp.status = falcon.HTTP_200
            return True
        elif isinstance(result, int):
            if result == error_code.CACHE_BUS_COOKIE_ERROR:
                raise falcon.HTTPInternalServerError(
                    description='api server not found cookie.')
            elif result == error_code.CACHE_BUS_USER_ERROR:
                raise falcon.HTTPForbidden(
                    description='NKUST server not found user data.')
            elif result == error_code.BUS_TIMEOUT_ERROR:
                raise falcon.HTTPServiceUnavailable(description='timeout')

        raise falcon.HTTPInternalServerError(
            description='something error ?')
