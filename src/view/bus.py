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
            r'^([1-9][0-9]{3})-([01]?[0-9]?[0-9])-([01]?[0-9]?[0-9])$')
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
            if len(reslut) < 100:
                resp.status = falcon.HTTP_204
                return True
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

class busUserReservations:

    @falcon.before(bus_login_cache_required)
    def on_get(self, req, resp):

        payload = req.context['user']['user']
        result = bus_cache.bus_reservations_record(
            username=payload['username'])

        if isinstance(result, str):
            if len(result) < 50:
                resp.status = falcon.HTTP_204
                return True
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

    @falcon.before(bus_login_cache_required)
    def on_delete(self, req, resp):
        payload = req.context['user']['user']
        if req.get_param('cancelKey') == None or req.get_param('cancelKey') == '':
            raise falcon.HTTPBadRequest(description='params error')

        result = bus_cache.bus_reserve_book(
            username=payload['username'], kid=req.get_param('cancelKey'), action=False)

        if isinstance(result, dict):
            if not result['success']:
                resp.media = {
                    "errorCode": 454,
                    "description": "取消失敗，未知錯誤"
                }
                resp.status = falcon.HTTP_403
            elif result['success']:
                resp.media = {'success': True}
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
