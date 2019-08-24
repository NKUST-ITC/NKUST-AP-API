import re

import falcon

from cache import bus_cache
from utils import error_code
from utils.util import bus_login_cache_required


class busViolationRecord:

    @falcon.before(bus_login_cache_required)
    def on_get(self, req, resp):

        payload = req.context['user']['user']

        reslut = bus_cache.bus_violation(
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
            elif reslut == error_code.BUS_TIMEOUT_ERROR:
                raise falcon.HTTPServiceUnavailable(description='timeout')

        raise falcon.HTTPInternalServerError(
            description='something error ?')
