import json
import datetime
import falcon


from utils import config
from cache import school_announcements_cache as sac_cache
from utils import error_code


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
