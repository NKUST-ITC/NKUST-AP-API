import json
import datetime
import falcon

from auth import jwt_auth
from utils.util import max_body
from utils import config
from cache import ap_cache
from utils import error_code


class userInfo:

    def on_get(self, req, resp):
        # jwt payload
        payload = req.context['user']['user']

        user_info = ap_cache.user_info(
            username=payload['username'], password=payload['password'])

        if isinstance(user_info, dict):
            resp.media = user_info
            resp.status = falcon.HTTP_200
            return True
        elif user_info == error_code.CACHE_WEBAP_SERVER_ERROR:
            resp.status = falcon.HTTP_503
            raise falcon.HTTPServiceUnavailable()
        elif user_info == error_code.CACHE_WEBAP_LOGIN_FAIL:
            resp.status = falcon.HTTP_401
            return True
        else:
            raise falcon.HTTPInternalServerError(
                description='something error ?')


class userSemesters:

    def on_get(self, req, resp):

        semesters_data = ap_cache.semesters()
        if isinstance(semesters_data, str):
            resp.body = semesters_data
            resp.media = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
            return True
        # error handle
        elif isinstance(semesters_data, int):
            if semesters_data == error_code.SEMESTERS_QUERY_ERROR:
                resp.status = falcon.HTTP_500
                raise falcon.HTTPInternalServerError(
                    description="SEMESTERS QUERY ERROR")

            elif semesters_data == error_code.WEBAP_ERROR:
                resp.status = falcon.HTTP_503
                raise falcon.HTTPServiceUnavailable()

        else:
            raise falcon.HTTPInternalServerError(
                description='something error ?')
