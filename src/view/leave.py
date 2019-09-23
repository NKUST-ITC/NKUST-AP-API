import json
import datetime
import falcon

from auth import jwt_auth
from utils.util import leave_login_cache_required
from utils import config
from cache import leave_cache
from utils import error_code


class leave_list:

    @falcon.before(leave_login_cache_required)
    def on_get(self, req, resp):
        # jwt payload
        payload = req.context['user']['user']
        if req.get_param('year') == None and req.get_param('semester') == None:
            raise falcon.HTTPBadRequest(description='params error')

        if len(req.get_param('year')) > 4 or len(req.get_param('semester')) > 2:
            raise falcon.HTTPBadRequest(description='params error')

        leave_dict = leave_cache.get_leave_list(
            username=payload['username'],
            year=req.get_param('year'), semester=req.get_param('semester'))

        if isinstance(leave_dict, str):
            resp.body = leave_dict
            resp.media = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
            return True
        raise falcon.HTTPInternalServerError(
            description='something error ?')


class leave_submit_info:

    @falcon.before(leave_login_cache_required)
    def on_get(self, req, resp):
        # jwt payload
        payload = req.context['user']['user']

        submit_info = leave_cache.get_submit_info(username=payload['username'])

        if isinstance(submit_info, str):
            resp.body = submit_info
            resp.media = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
            return True
        raise falcon.HTTPInternalServerError(
            description='something error ?')

