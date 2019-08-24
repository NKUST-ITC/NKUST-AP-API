import re

import falcon

from cache import bus_cache
from utils import error_code
from utils.util import bus_login_cache_required


class busTimeTable:

    @falcon.before(bus_login_cache_required)
    def on_get(self, req, resp):

        payload = req.context['user']['user']
        if req.get_param('date') == None:
            raise falcon.HTTPBadRequest(description='params error')
        date_pattern = re.compile(
            r'^([1-9][0-9]{3})-(\+?{[1-9][0-9]|[0-9][1-9]|[1-9]}{0,1})-(\+?{[1-9][0-9]|[0-9][1-9]|[1-9]}{0,1})$')
        regex_match = date_pattern.match(req.get_param('date'))
        if not regex_match:
            raise falcon.HTTPBadRequest(description='params value error')
        if int(regex_match[2]) > 12 or int(regex_match[3]) > 31:
            raise falcon.HTTPBadRequest(description='params value error')

        reslut = bus_cache.bus_query(
            username=payload['username'],
            year=int(regex_match[1]),
            month=int(regex_match[2]),
            day=int(regex_match[3]))

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
