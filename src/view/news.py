import falcon

from cache import school_announcements_cache as sac_cache
from utils import error_code
from news import news

class acadNews:

    auth = {
        'exempt_methods': ['GET']
    }

    def on_get(self, req, resp):

        if req.get_param('page') == None:
            raise falcon.HTTPBadRequest(description='params error')
        try:
            int(req.get_param('page'))
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
