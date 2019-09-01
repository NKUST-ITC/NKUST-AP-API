import falcon

from news import news


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
        if news_data is []:
            resp.status = falcon.HTTP_204
            return True

        if isinstance(news_data, list):

            resp.media = {
                'data': news_data
            }
            resp.status = falcon.HTTP_200
            return True

        raise falcon.HTTPInternalServerError()
