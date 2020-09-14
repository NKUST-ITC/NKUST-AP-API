import requests
from utils import config


def login(username: str, password: str) -> bool:

    if config.LOGIN_API_KEY is None:
        return False

    data = {
        "apiKey": config.LOGIN_API_KEY,
        "userId": username,
        "userPw": password,
        "userKeep": 0
    }

    req = requests.post(
        "https://inkusts.nkust.edu.tw/User/DoLogin2", data=data)
    if req.status_code == 200:
        try:
            return req.json()['success']
        except:
            pass
    return False
