import datetime
import json

import falcon

from auth import jwt_auth
from cache import ap_cache, api_cache
from utils import config, error_code
from utils.util import max_body


class ApiLogin:
    auth = {
        'auth_disabled': True
    }
    @falcon.before(max_body(64 * 1024))
    def on_post(self, req, resp):

        req_json = json.loads(req.bounded_stream.read(), encoding='utf-8')
        # check json key
        for key in req_json.keys():
            if key not in ['username', 'password']:
                # return status code 406  not acceptable
                raise falcon.HTTPNotAcceptable(falcon.HTTP_NOT_ACCEPTABLE)

        for value in req_json.values():
            if len(value) > 64:
                # return status code 406  not acceptable for value too long
                raise falcon.HTTPPayloadTooLarge("value too long.")

        # login to webap for check user acceptable
        login_status = ap_cache.login(username=req_json['username'],
                                      password=req_json['password'])

        if login_status == error_code.CACHE_WENAP_LOGIN_SUCCESS:
            JWT_token = jwt_auth.get_auth_token(user_payload=req_json)
            resp.media = {
                'token': JWT_token,
                'expireTime': datetime.datetime.isoformat(datetime.datetime.now() + datetime.timedelta(seconds=config.JWT_EXPIRE_TIME))
            }
            resp.status = falcon.HTTP_200
            return True
        elif login_status == error_code.CACHE_WEBAP_LOGIN_FAIL:
            resp.status = falcon.HTTP_401
            return True
        elif login_status == error_code.CACHE_WEBAP_SERVER_ERROR:
            resp.status = falcon.HTTP_503
            raise falcon.HTTPServiceUnavailable()

        else:
            raise falcon.HTTPBadRequest()


class ServerStatus:
    auth = {
        'auth_disabled': True
    }

    def on_get(self, req, resp):

        server_status = api_cache.server_status()

        if isinstance(server_status, str):
            resp.body = server_status
            resp.media = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
            return True
        raise falcon.HTTPInternalServerError(
            description='something error ?')
