import falcon

from utils.util import library_login_cache_required
from cache import library_cache


class userInfo:

    @falcon.before(library_login_cache_required)
    def on_get(self, req, resp):
        # jwt payload
        payload = req.context['user']['user']

        user_info = library_cache.userinfo(
            username=payload['username'])

        if isinstance(user_info, str):
            resp.body = user_info
            resp.media = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
            return True
        raise falcon.HTTPInternalServerError(
            description='something error ?')
