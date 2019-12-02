
import hashlib
import pickle
import json
import redis
import requests

from crawler import school_announcements_crawler as sac_crawler
from utils import error_code
from utils import config
from utils.config import REDIS_URL

red_string = redis.StrictRedis.from_url(
    url=REDIS_URL, db=4, charset="utf-8", decode_responses=True)


def acad_cache(page):
    """acad news.

    Args:
        page ([int]): page

    Returns:
        [str]: result type is json
        [int]: ACAD_ERROR
               ACAD_TIMEOUT

    """
    acad_cache_name = "news_acad_{page}".format(page=page)
    if red_string.exists(acad_cache_name):
        return red_string.get(acad_cache_name)

    notification_data = sac_crawler.acad(page=page-1)
    if isinstance(notification_data, list):
        return_data = {
            'data': {
                'page': int(page),
                'notification': notification_data
            }
        }
        _dumps = json.dumps(return_data, ensure_ascii=False)
        red_string.set(name=acad_cache_name, value=_dumps,
                       ex=config.CACHE_ACAD_EXPIRE_TIME)

        return _dumps
    return notification_data
