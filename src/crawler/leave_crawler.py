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


def get_leave_list(session, year, semester):
    """[summary]

    Args:
        session ([type]): [description]
        year ([type]): [description]
        semester ([type]): [description]

    Returns:
        [list]: leave list.
        [bool]: False, fail case.
    """

    req = session.get("http://leave.nkust.edu.tw/AK002MainM.aspx")

    if req.status_code != 200:
        return error_code.LEAVE_LOGIN_FAIL

    root = etree.HTML(req.text)

    form = {}
    for i in root.xpath("//input"):
        form[i.attrib["name"]] = i.attrib[
            "value"] if "value" in i.attrib else ""

    try:
        del form['ctl00$ButtonLogOut']
    except:
        return False

    form[
        'ctl00$ContentPlaceHolder1$SYS001$DropDownListYms'] = "%s-%s" % (year, semester)

    r = session.post(
        "http://leave.nkust.edu.tw/AK002MainM.aspx", data=form)
    root = etree.HTML(r.text)

    tr = root.xpath("//table")[-1]
    timecode = root.xpath('//table[@class="mGridDetail"]/tr[1]/th')
    timecode = [i.text for i in timecode][4:]

    leave_list = []

    # Delete row id, leave id, teacher quote
    for r_index, r in enumerate(tr):
        r = list(map(lambda x: x.replace("\r", "").
                     replace("\n", "").
                     replace("\t", "").
                     replace(u"\u3000", "").
                     replace(" ", ""),
                     r.itertext()
                     ))

        if not r[0]:
            del r[0]
        if not r[-1]:
            del r[-1]

        leave_list.append(r)
    result = []
    for r in leave_list[1:]:
        i = len(r)-15
        for approved in range(4, i):
            r[3] += ' , '+r[approved]
        leave = {
            "leaveSheetId": r[1].replace("\xa0", ""),
            "date": r[2],
            "instructorsComment": r[3],
            "sections": [
                {"section": leave_list[0][index + 4], "reason": s}
                for index, s in enumerate(r[i:])
            ]
        }

        leave["sections"] = list(
            filter(lambda x: x["reason"], leave["sections"]))
        result.append(leave)
    return [result, timecode]
