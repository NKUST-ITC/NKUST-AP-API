
import datetime
import json

import redis

from utils import config, error_code

red_news = redis.StrictRedis.from_url(
    url=config.REDIS_URL, db=8, charset="utf-8", decode_responses=True)


def get_news(news_id, all_news=None):
    """get a news.

    Args:
        all_news ([list]): must be sorted, get this data from _get_all_news.
        news_id ([int]): news id

    Returns:
        [dict]: news data
        [bool]: False
        [None]: not found news.
    """
    if not all_news:
        all_news = _get_all_news()
    if len(all_news) < 1:
        return None
    temp_news_index = -1
    news_next = {}
    news_last = {}

    for index, value in enumerate(all_news):
        if value['id'] == news_id:
            temp_news_index = index
            try:
                news_next = all_news[index+1]
            except:
                news_next = {}
            try:
                news_last = all_news[index-1]
                if index-1 < 0:
                    news_last = {}
            except:
                news_last = {}

    if temp_news_index < 0:
        # not found news
        return None

    # mix news next id and news last id to dict
    all_news[temp_news_index]['nextId'] = news_next.get('id', None)
    all_news[temp_news_index]['lastId'] = news_last.get('id', None)

    return all_news[temp_news_index]


def get_all_news():
    # public
    all_news_data = _get_all_news()
    return [get_news(news_id=i['id'], all_news=all_news_data) for i in all_news_data]


def _get_all_news():
    # private
    news = sorted([json.loads(red_news.get(i))
                   for i in red_news.scan_iter()], key=lambda k: k['id'])
    return news


def time_format(time_str):
    """Change world all timezone to utc.

    Args:
        time_str ([str]): '2019-08-31T06:33:29Z'
                          '2019-08-31T06:33:29H'
                          or more ...
        https://en.wikipedia.org/wiki/List_of_military_time_zones

    Returns:
        [datetime.datetime]: utc datetime 
        [bool]: False error format.
    """
    try:
        negative = -1
        time_zone = {
            "A": 1,
            "B": 2,
            "C": 3,
            "D": 4,
            'E': 5,
            'F': 6,
            'G': 7,
            'H': 8,
            'I': 9,
            'K': 10,
            'L': 11,
            'M': 12,
            'N': 1*negative,
            'O': 2*negative,
            'P': 3*negative,
            'Q': 4*negative,
            'R': 5*negative,
            'S': 6*negative,
            'T': 7*negative,
            'U': 8*negative,
            'V': 9*negative,
            'W': 10*negative,
            'X': 11*negative,
            'Y': 12*negative,
            'Z': 0
        }[time_str[-1]]
    except:
        return False
    raw_time = datetime.datetime.strptime(time_str[:-1], "%Y-%m-%dT%H:%M:%S")
    utc_time = raw_time + datetime.timedelta(hours=-time_zone)
    return utc_time


def add_news(**kwargs):
    """Add news to redis.

    Kwargs:
        title   [str]:     Required.
        imgUrl [str]:     Optional.
        url     [str]:     Link, optional.
        weight  [int]:     news weight,optional.
        description [str]: Optional.
        expireTime  [str]: ISO 8601, must have timezone at last character.

            2019-09-2T11:33:29H
            2019-09-2T11:33:29Z
            2019-09-2T11:33:29A
            ...

    Returns:
        [bool]: False
        [int]: Success, return news id.
    """
    title = kwargs.get('title', False)
    if not title:
        return False

    news_name = "news_{news_id}"
    id_count = len([i for i in red_news.scan_iter()])
    news_id = 0
    for id_ in range(id_count+1):
        if not red_news.exists(news_name.format(news_id=id_)):
            news_id = id_
            break

    news_data = {
        "title": title,
        "id": news_id,
        "publishedAt": datetime.datetime.utcnow().isoformat(timespec="seconds")+"Z",
        "weight": int(kwargs.get('weight', 0)),
        "imgUrl": kwargs.get('imgUrl', None),
        "url": kwargs.get('url', None),
        "description": kwargs.get('description', None),
        "expireTime": None
    }
    expire_time_seconds = kwargs.get('expireTime', None)
    if kwargs.get('expireTime', False):
        utc = time_format(kwargs.get('expireTime', False))
        expire_time_seconds = int(
            (utc-datetime.datetime.utcnow()).total_seconds())
        if expire_time_seconds < 0:
            expire_time_seconds = None
        else:
            news_data["expireTime"] = time_format(kwargs.get(
                'expireTime', False)).isoformat(timespec="seconds")+"Z"
    data_dumps = json.dumps(news_data, ensure_ascii=False)

    red_news.set(name=news_name.format(news_id=news_id),
                 value=data_dumps, ex=expire_time_seconds)
    return news_id


def update_news(news_id=None, **kwargs):
    """Update news.

    Args:
        news_id ([int]): news id.

    Kwargs:
        title   [str]:     Optional.
        img_url [str]:     Optional.
        url     [str]:     Link, optional.
        weight  [int]:     news weight,optional.
        description [str]: Optional.
        expireTime  [str]: ISO 8601, must have timezone at last character.

            2019-09-2T11:33:29H
            2019-09-2T11:33:29Z
            2019-09-2T11:33:29A
            ...

    Returns:
        [bool]: True
        [int]: NEWS_NOT_FOUND
               NEWS_ERROR
               NEWS_LOSS_ARG
    """
    if news_id == None:
        return error_code.NEWS_ERROR
    title = kwargs.get('title', False)
    if not title:
        return error_code.NEWS_LOSS_ARG

    news_name = "news_{news_id}".format(news_id=news_id)
    if not red_news.exists(news_name):
        return error_code.NEWS_NOT_FOUND
    origin_news = json.loads(red_news.get(news_name))

    news_data = {
        "title": kwargs.get('title', origin_news.get('title', "")),
        "id": int(news_id),
        "publishedAt": datetime.datetime.utcnow().isoformat(timespec="seconds")+"Z",
        "weight": int(kwargs.get('weight', int(origin_news.get('weight', 0)))),
        "imgUrl": kwargs.get('img_url', origin_news.get('imgUrl', None)),
        "url": kwargs.get('url', origin_news.get('url', None)),
        "description": kwargs.get('description', origin_news.get('description', None)),
        "expireTime": kwargs.get('expireTime', origin_news.get('expireTime', None))
    }
    expire_time_seconds = kwargs.get(
        'expireTime', origin_news.get('expireTime', None))
    if kwargs.get('expireTime', origin_news.get('expireTime', False)):
        utc = time_format(kwargs.get(
            'expireTime', origin_news.get('expireTime', False)))
        expire_time_seconds = int(
            (utc-datetime.datetime.utcnow()).total_seconds())
        if expire_time_seconds < 0:
            expire_time_seconds = None
        else:
            news_data["expireTime"] = time_format(kwargs.get(
                'expireTime', False)).isoformat(timespec="seconds")+"Z"
    data_dumps = json.dumps(news_data, ensure_ascii=False)

    red_news.set(name=news_name,
                 value=data_dumps, ex=expire_time_seconds)
    return True


def remove_news(news_id=None):
    """remove news.

    Args:
        news_id ([int]): news id.

    Returns:
        [bool]: True
        [int]: NEWS_NOT_FOUND
               NEWS_ERROR
    """
    if news_id == None:
        return error_code.NEWS_ERROR

    news_name = "news_{news_id}".format(news_id=news_id)
    if not red_news.exists(news_name):
        return error_code.NEWS_NOT_FOUND

    red_news.delete(news_name)
    return True
