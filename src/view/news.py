import datetime
import json

import falcon
import redis

from auth import jwt_auth
from cache import school_announcements_cache as sac_cache
from news import news
from utils import config, error_code, util
from utils.util import (falcon_admin_required, max_body,
                        webap_login_cache_required)

red_auth_token = redis.StrictRedis.from_url(
    url=config.REDIS_URL, db=6, charset="utf-8", decode_responses=True)


class newsAdminLogin:
    auth = {
        'exempt_methods': ['POST']
    }
    @falcon.before(max_body(64 * 1024))
    def on_post(self, req, resp):

        req_json = json.loads(req.bounded_stream.read(), encoding='utf-8')
        # check json key
        for key in req_json.keys():
            if key not in ['username', 'password']:
                # return status code 406  not acceptable
                raise falcon.HTTPNotAcceptable(falcon.HTTP_NOT_ACCEPTABLE)

        if req_json['username'] != config.NEWS_ADMIN_ACCOUNT and req_json['password'] != config.NEWS_ADMIN_PASSWORD:
            raise falcon.HTTPUnauthorized()

        token = util.randStr(32)
        req_json['token'] = token
        red_auth_token.set(
            name="{username}_{token}".format(
                username=req_json['username'],
                token=token),
            value='',
            ex=config.ADMIN_JWT_EXPIRE_TIME)
        JWT_token = jwt_auth.get_auth_token(user_payload=req_json)
        resp.media = {
            'token': JWT_token,
            'expireTime': (datetime.datetime.utcnow() + datetime.timedelta(seconds=config.ADMIN_JWT_EXPIRE_TIME)).isoformat(timespec='seconds')+"Z"
        }
        resp.media['isAdmin'] = True

        resp.status = falcon.HTTP_200
        return True

    def on_delete(self, req, resp):

        payload = req.context['user']['user']
        redis_token_name = "{username}_{token}".format(
            username=payload['username'],
            token=payload['token'])
        red_auth_token.delete(redis_token_name)
        resp.status = falcon.HTTP_205


class acadNews:

    auth = {
        'exempt_methods': ['GET']
    }

    def on_get(self, req, resp):

        if req.get_param('page') == None:
            raise falcon.HTTPBadRequest(description='params error')
        try:
            int(req.get_param('page'))
            if int(req.get_param('page')) < 1:
                raise falcon.HTTPBadRequest(description='params error')
        except:
            raise falcon.HTTPBadRequest(description='params error')

        acad_news_data = sac_cache.acad_cache(page=int(req.get_param('page')))

        if isinstance(acad_news_data, str):
            resp.body = acad_news_data
            resp.media = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
            return True
        elif acad_news_data == error_code.ACAD_TIMEOUT:
            resp.status = falcon.HTTP_503
            return True

        raise falcon.HTTPInternalServerError(
            description='something error ?')


class Announcements:

    auth = {
        'exempt_methods': ['GET']
    }

    def on_get(self, req, resp):
        '/news​/announcements'
        news_data = news.get_all_news()
        if len(news_data) > 0:
            resp.media = news_data[0]
            resp.status = falcon.HTTP_200
            return True
        else:
            resp.status = falcon.HTTP_204
            return True
        raise falcon.HTTPInternalServerError()


class AnnouncementsById:

    auth = {
        'exempt_methods': ['GET']
    }

    def on_get(self, req, resp, news_id):
        '/news​/announcements/{news_id}'
        try:
            news_id = int(news_id)
        except:
            raise falcon.HTTPBadRequest()

        news_data = news.get_news(int(news_id))
        if isinstance(news_data, dict):
            resp.media = news_data
            resp.status = falcon.HTTP_200
            return True
        elif news_data is None:
            resp.status = falcon.HTTP_204
            return True

        raise falcon.HTTPInternalServerError()


class AnnouncementsAll:

    auth = {
        'exempt_methods': ['GET']
    }

    def on_get(self, req, resp):
        '/news/announcements/all'

        news_data = news.get_all_news()
        if news_data == []:
            resp.status = falcon.HTTP_204
            return True

        if isinstance(news_data, list):

            resp.media = {
                'data': news_data
            }
            resp.status = falcon.HTTP_200
            return True

        raise falcon.HTTPInternalServerError()


class NewsAdd:

    @falcon.before(max_body(64 * 1024))
    @falcon.before(webap_login_cache_required)
    @falcon.before(falcon_admin_required)
    def on_post(self, req, resp):

        req_json = json.loads(req.bounded_stream.read(), encoding='utf-8')
        # check json key
        for key in req_json.keys():
            if key not in ['title', 'description', 'imgUrl', 'url', 'weight', 'expireTime']:
                raise falcon.HTTPBadRequest()
        if not isinstance(req_json.get('weight', 0), int):
            raise falcon.HTTPBadRequest(description='weight wrong type.')
        result = news.add_news(**req_json)
        if isinstance(result, int):
            resp.media = {
                'id': result
            }
            resp.status = falcon.HTTP_200
            return True
        elif result is False:
            raise falcon.HTTPBadRequest()
        raise falcon.HTTPInternalServerError()


class NewsUpdate:

    @falcon.before(max_body(64 * 1024))
    @falcon.before(webap_login_cache_required)
    @falcon.before(falcon_admin_required)
    def on_put(self, req, resp, news_id):

        req_json = json.loads(req.bounded_stream.read(), encoding='utf-8')
        # check json key
        for key in req_json.keys():
            if key not in ['title', 'description', 'imgUrl', 'url', 'weight', 'expireTime']:
                raise falcon.HTTPBadRequest()
        if not isinstance(req_json.get('weight', 0), int):
            raise falcon.HTTPBadRequest(description='weight wrong type.')
        result = news.update_news(news_id=news_id, **req_json)
        if result is True:
            resp.media = {
                "message": "Update success,id {id}.".format(id=news_id)
            }
            resp.status = falcon.HTTP_200
            return True

        if isinstance(result, int):
            if result == error_code.NEWS_ERROR:
                raise falcon.HTTPBadRequest()
            elif result == error_code.NEWS_NOT_FOUND:
                raise falcon.HTTPForbidden(description='not found news')
            elif result == error_code.NEWS_LOSS_ARG:
                raise falcon.HTTPBadRequest()

        raise falcon.HTTPInternalServerError()


class NewsRemove:

    @falcon.before(webap_login_cache_required)
    @falcon.before(falcon_admin_required)
    def on_delete(self, req, resp, news_id):

        result = news.remove_news(news_id=news_id)
        if result is True:
            resp.media = {
                "message": "Remove success,id {id}.".format(id=news_id)
            }
            resp.status = falcon.HTTP_200
            return True

        if isinstance(result, int):
            if result == error_code.NEWS_ERROR:
                raise falcon.HTTPBadRequest()
            elif result == error_code.NEWS_NOT_FOUND:
                raise falcon.HTTPForbidden(description='not found news')
        raise falcon.HTTPInternalServerError()
