import requests
from lxml import etree

from utils import config, error_code
import datetime


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


def get_submit_info(session):
    # more return detail in swagger.
    main_url = 'http://leave.nkust.edu.tw/CK001MainM.aspx'
    req = session.get(main_url)
    root = etree.HTML(req.text)

    form_data = {i.attrib["name"]: i.attrib["value"] for i in root.xpath(
        "//input") if i.attrib["name"] != "ctl00$ButtonLogOut"}

    req = session.post(url=main_url, data=form_data)
    root = etree.HTML(req.text)

    form_data = {i.attrib.get("name"): i.attrib.get("value", "") for i in root.xpath("//input") if i.attrib["name"] not in [
        "ctl00$ButtonLogOut", 'ctl00$ContentPlaceHolder1$CK001$ButtonQuery', 'ctl00$ContentPlaceHolder1$CK001$ButtonClear', 'ctl00$ContentPlaceHolder1$CK001$ButtonPreview']}

    now = datetime.datetime.now()
    fake_date = "{tern_year}/{m}/{d}".format(
        tern_year=str(now.year-1911), m=now.month, d=now.day)

    form_data['ctl00$ContentPlaceHolder1$CK001$DateUCCBegin$text1'] = fake_date
    form_data['ctl00$ContentPlaceHolder1$CK001$DateUCCEnd$text1'] = fake_date

    req = session.post(url=main_url, data=form_data)
    root = etree.HTML(req.text)

    leave_value = root.xpath(
        "//*[@id='ContentPlaceHolder1_CK001_RadioButtonListOption']//input")
    leave_label = root.xpath(
        "//*[@id='ContentPlaceHolder1_CK001_RadioButtonListOption']//label")
    teacher = root.xpath(
        "//select[@id='ContentPlaceHolder1_CK001_ddlTeach']/option[@selected='selected']")
    time_code = root.xpath(
        "//*[@id='ContentPlaceHolder1_CK001_GridViewMain']//tr[1]//th")

    result = {}
    if len(teacher) == 1:
        result['tutors'] = {
            'name': teacher[0].text,
            'id': teacher[0].attrib.get("value", None)
        }
    else:
        result['tutors'] = {
            'name': None,
            'id': None
        }
    result['type'] = [{'title': label.text, 'id': value.attrib.get(
        'value', None)} for value, label in zip(leave_value, leave_label)]

    result['timeCode'] = [i.text for i in time_code[3:]]

    return result
