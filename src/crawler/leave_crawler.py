import requests
from lxml import etree

from utils import config, error_code


def login(session, username, password):
    """login to leave system

    Args:
        session ([request.session]): requests session
        username ([str]): username of NKUST ap system, actually your NKUST student id.
        password ([str]): password of NKUST ap system.

    Returns:
        [int]: LEAVE_LOGIN_TIMEOUT(801)
               LEAVE_LOGIN_SUCCESS (802)
               LEAVE_LOGIN_FAIL (803)

    """
    try:
        session.headers.update({
            'Origin': 'http://leave.nkust.edu.tw',
            'Upgrade-Insecure-Requests': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://leave.nkust.edu.tw/LogOn.aspx',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6'
        })
        req = session.get("http://leave.nkust.edu.tw/LogOn.aspx",
                          timeout=config.LEAVE_LOGIN_TIMEOUT)
    except requests.exceptions.Timeout:
        return error_code.LEAVE_LOGIN_TIMEOUT
    root = etree.HTML(req.text)

    form = {}
    for i in root.xpath("//input"):
        form[i.attrib['name']] = ""
        if "value" in i.attrib:
            form[i.attrib['name']] = i.attrib['value']

    form['Login1$UserName'] = username
    form['Login1$Password'] = password
    form['__EVENTTARGET	'] = ''
    form['__EVENTARGUMENT	'] = ''

    r = session.post('http://leave.nkust.edu.tw/LogOn.aspx',
                     data=form, allow_redirects=False)

    if r.status_code == 302:
        session.get('http://leave.nkust.edu.tw/masterindex.aspx')
        return error_code.LEAVE_LOGIN_SUCCESS
    else:
        return error_code.LEAVE_LOGIN_FAIL
