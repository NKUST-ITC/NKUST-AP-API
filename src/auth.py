import redis
from falcon_auth import FalconAuthMiddleware, JWTAuthBackend

from utils import util
from utils.config import REDIS_URL
from utils.config import JWT_EXPIRE_TIME

red_auth = redis.StrictRedis.from_url(
    url=REDIS_URL, db=4, charset="utf-8", decode_responses=True)

if red_auth.exists('secret_key'):
    SECRET_KEY = red_auth.get('secret_key')
else:
    # generate key and save to redis
    SECRET_KEY = util.randStr(32)
    red_auth.set('secret_key', SECRET_KEY)


def user_loader(client_submitted_jwt):
    """can make basic check in this function.

    Args:
        client_submitted_jwt ([dict]): after decode by JWT

    Returns:
        [dict]: after check raw_data
    """
    return client_submitted_jwt


jwt_auth = JWTAuthBackend(user_loader,
                          secret_key=SECRET_KEY,
                          auth_header_prefix='Bearer',
                          leeway=JWT_EXPIRE_TIME)
auth_middleware = FalconAuthMiddleware(jwt_auth)
