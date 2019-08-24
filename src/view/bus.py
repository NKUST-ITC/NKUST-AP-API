import re

import falcon

from cache import bus_cache
from utils import error_code
from utils.util import bus_login_cache_required


class busUserReservations:

    @falcon.before(bus_login_cache_required)
    def on_get(self, req, resp):

        payload = req.context['user']['user']
        result = bus_cache.bus_reservations_record(
            username=payload['username'])

        if isinstance(result, str):
            resp.body = result
            resp.media = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
            return True
        # error handle
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
