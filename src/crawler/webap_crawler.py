from lxml import etree
import requests
from utils import error_code
from utils import config

LOGIN_TIMEOUT = config.WEBAP_LOGIN_TIMEOUT
AP_BASE_URL = "https://webap.nkust.edu.tw"
AP_HEADER_URL = 'https://webap.nkust.edu.tw/nkust/f_head.jsp'
#: AP system login url
AP_LOGIN_URL = AP_BASE_URL + "/nkust/perchk.jsp"

#: AP system general query url, with two args,
#  first: prefix of qid, second: qid
AP_QUERY_URL = AP_BASE_URL + "/nkust/%s_pro/%s.jsp"

#: Query timeout
QUERY_TIMEOUT = config.WEPAP_QUERY_TIMEOUT


def login(session, username, password, timeout=LOGIN_TIMEOUT):
    """login to webap

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


def graduation_threshold(session):
    """get graduation threshold
        url : "/user/graduation-threshold"

    Args:
        session ([requests.session]): must be login webap!

    Returns:
        [requests.models.Response]: requests response
        other error will return False
    """

    # post it, it will return Aength.kuas.edu.tw cookie
    Aength_login = session.post('https://webap.nkust.edu.tw/nkust/fnc.jsp',
                                data={'fncid': 'AG635'})
    # get post data
    try:
        root = etree.HTML(Aength_login.text)
        term_form_xpath = root.xpath('//input[@type="hidden"]')
        term_form = {i.values()[1]: i.values()[-1] for i in term_form_xpath}
    except:
        return False

    # final post
    query_url = 'http://Aength.kuas.edu.tw/AUPersonQ.aspx'

    res = session.post(url=query_url, data=term_form)

    return res


def graduate_user_info(session):
    """Get less user info from webap header.

    Args:
        session ([requests.session]): must be login webap!

    Returns:
        [requests.models.Response]: requests response
        other error will return False
    """
    req = session.get(url=AP_HEADER_URL, timeout=LOGIN_TIMEOUT)
    if req.status_code == 200:
        return req
    return False


def query(session, qid, **kwargs):
    """AP system query

    Args:
        session ([requests.session]): after load cookies
        qid ([str]): url qid

        kwargs:
            (e.g.)
            ag_query(session=session, qid='ag008',
                           yms='107,2', arg01='107', arg02='2')

            post data will = {
                'yms':'107,2',
                'arg01':'107',
                'arg02':'2'
            }

    Returns:
        [requests.models.Response]: requests response

        [bool]: something error will return False
    """

    try:
        req = session.post(AP_QUERY_URL % (qid[:2], qid),
                           data=kwargs)
        return req
    except:
        return False

    return False
