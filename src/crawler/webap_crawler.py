from lxml import etree
import requests
from utils import error_code
from utils import config

LOGIN_TIMEOUT = config.WEBAP_LOGIN_TIMEOUT
AP_BASE_URL = "https://webap.nkust.edu.tw"

#: AP system login url
AP_LOGIN_URL = AP_BASE_URL + "/nkust/perchk.jsp"

#: AP system general query url, with two args,
#  first: prefix of qid, second: qid
AP_QUERY_URL = AP_BASE_URL + "/nkust/%s_pro/%s.jsp"

#: AP guest account
AP_GUEST_ACCOUNT = "guest"

#: AP guest password
AP_GUEST_PASSWORD = "123"

#: Query timeout
QUERY_TIMEOUT = config.WEPAP_QUERY_TIMEOUT


def login(session, username, password, timeout=LOGIN_TIMEOUT):
    """[summary]

    Args:
        session ([request.session]): requests session
        username ([str]): username of NKUST ap system, actually your NKUST student id.
        password ([str]): password of NKUST ap system.
        timeout ([int], optional): Defaults is LOGIN_TIMEOUT.

    Returns:
        [int]: utils/error_code.py
               error_code.WENAP_login_success(100)
               error_code.WEBAP_login_fail (101)
               error_code.WEBAP_server_error (102)
               error_code.WEBAP_error (103)

    """
    payload = {
        "uid": username,
        "pwd": password
    }

    # If timeout, return false
    try:
        r = session.post(
            AP_LOGIN_URL,
            data=payload,
            timeout=timeout
        )
    except requests.exceptions.Timeout:
        return error_code.WEBAP_SERVER_ERROR
    # print(r.text)
    root = etree.HTML(r.text)
    try:
        is_login = root.xpath("/html/body/script")[0].text.find('alert')

        if is_login == -1:
            # login success
            return error_code.WENAP_LOGIN_SUCCESS
        elif is_login >= 0:
            return error_code.WEBAP_LOGIN_FAIL
    except Exception as error:
        print(error)
        return error_code.WEBAP_ERROR

    return error_code.WEBAP_ERROR
