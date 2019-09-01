import redis
from falcon_auth import FalconAuthMiddleware, JWTAuthBackend

from utils import util
from utils.config import REDIS_URL
from utils.config import JWT_EXPIRE_TIME

red_auth = redis.StrictRedis.from_url(
    url=REDIS_URL, db=4, charset="utf-8", decode_responses=True)

red_auth_token = redis.StrictRedis.from_url(
    url=REDIS_URL, db=6, charset="utf-8", decode_responses=True)

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
    redis_token_name = "{username}_{token}".format(
        username=client_submitted_jwt['user']['username'],
        token=client_submitted_jwt['user']['token'])

    if red_auth_token.exists(redis_token_name):
        return client_submitted_jwt
    return False


jwt_auth = JWTAuthBackend(user_loader,
                          secret_key=SECRET_KEY,
                          auth_header_prefix='Bearer',
                          leeway=60,
                          expiration_delta=JWT_EXPIRE_TIME)
auth_middleware = FalconAuthMiddleware(jwt_auth)
