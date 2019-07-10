import os


try:
    REDIS_URL = os.environ['REDIS_URL']
except KeyError:
    REDIS_URL = 'redis://127.0.0.1:6379'

JWT_EXPIRE_TIME = 3600

# crawler zone
WEBAP_LOGIN_TIMEOUT = 5
WEPAP_QUERY_TIMEOUT = 5

# cache zone
CACHE_USER_HASH_EXPIRE_TIME = 600
CACHE_WEBAP_COOKIE_EXPIRE_TIME = 600
