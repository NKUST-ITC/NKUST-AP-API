import os


try:
    REDIS_URL = os.environ['REDIS_URL']
except KeyError:
    REDIS_URL = 'redis://127.0.0.1:6379'

JWT_EXPIRE_TIME = 3600

# crawler zone
WEBAP_LOGIN_TIMEOUT = 5
WEPAP_QUERY_TIMEOUT = 5
#: AP guest account
AP_GUEST_ACCOUNT = "guest"
#: AP guest password
AP_GUEST_PASSWORD = "123"

# cache zone
CACHE_USER_HASH_EXPIRE_TIME = 600
CACHE_WEBAP_COOKIE_EXPIRE_TIME = 600
CACHE_WEBAP_QUERY_DEFAULT_EXPIRE_TIME = 600
CACHE_SEMESTERS_EXPIRE_TIME = 3600
# why course table expire time so long?
# read parse.py, it's worth it.
CACHE_COURSETABLE_EXPIRE_TIME = 60*60*6  # 6 hours