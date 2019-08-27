from lxml import etree
import requests
from utils import error_code
from utils import config


LIBRARY_BASE_URL = 'http://www.lib.nkust.edu.tw/portal'

LOGIN_URL = LIBRARY_BASE_URL+'/portal_login.php'

USER_PROFILE_URL = LIBRARY_BASE_URL+'/portal_profile.php'


def login(session, username, password):
    """Login to Library System 
    only nkust library (not Primo library)

    Args:
        session ([request.session]): requests session
        username ([str]): username of NKUST ap system, actually your NKUST student id.
        password ([str]): password of NKUST ap system.

    Returns:
        [int]: LIBRARY_LOGIN_SUCCESS(710)
               LIBRARY_LOGIN_FAIL(712)
               LIBRARY_ERROR(713)
    """

    #  form data
    payload = {
        'userid': username,
        'pass': password
    }
    try:
        resource = session.post(
            url=LOGIN_URL,
            data=payload,
            timeout=config.LIBRARY_LOGIN_TIMEOUT
        )
    except requests.exceptions.Timeout:
        return error_code.LIBRARY_ERROR

    if (resource.text).find('歡迎回來') > 0:
        return error_code.LIBRARY_LOGIN_SUCCESS
    elif resource.text.find('登入失敗') > 0:
        return error_code.LIBRARY_LOGIN_FAIL

    return error_code.LIBRARY_ERROR


def userInfo(session):

    connent = session.get(url=USER_PROFILE_URL)

    root = etree.HTML(connent.text)

    userDataTemp = root.xpath("//div[@class='idcard-right']//p")
    userRecordTemp = root.xpath(
        "//div[@class='uk-grid uk-grid-collapse color_primary']//span[@class='likes']")
    if len(userDataTemp) < 3:
        # something error
        return False

    userData = {
        'studentName': userDataTemp[0].text,
        'libraryId': userDataTemp[1].text,
        'department': userDataTemp[2].text,
        'record': {
            'borrowing': userRecordTemp[0].text,
            'reserve-rental': userRecordTemp[1].text,
            'userFine': userRecordTemp[2].text
        }
    }
    return userData
