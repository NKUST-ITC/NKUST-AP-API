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
    if len(leave_list) > 1:
        # count section length.
        section_len = len(leave_list[1])-len(leave_list[1][4:])
    for r in leave_list[1:]:
        for approved in range(4, section_len):
            # merge approved content in special cases.
            r[3] += ' , '+r[approved]
        leave = {
            "leaveSheetId": r[1].replace("\xa0", ""),
            "date": r[2],
            "instructorsComment": r[3],
            "sections": [
                {"section": leave_list[0][index + 4], "reason": s}
                for index, s in enumerate(r[section_len:])
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
    if req.status_code == 500:
        return error_code.LEAVE_SUBMIT_INFO_GRADUATE_ERROR
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
        result['tutor'] = {
            'name': teacher[0].text if teacher[0].text != "請選擇" else None,
            'id': teacher[0].attrib.get("value", None) if teacher[0].attrib.get("value", None) != "" else None
        }
    else:
        result['tutor'] = {
            'name': None,
            'id': None
        }
    if result['tutor']['name'] == None and result['tutor']['id'] == None:
        result['tutor'] = None
    result['type'] = [{'title': label.text, 'id': value.attrib.get(
        'value', None)} for value, label in zip(leave_value, leave_label)]

    result['timeCodes'] = [i.text for i in time_code[3:]]

    return result


def leave_submit(session, leave_data, proof_file=None, proof_file_name="test.jpg", proof_type='jpg'):

    main_url = 'http://leave.nkust.edu.tw/CK001MainM.aspx'
    req = session.get(main_url)
    root = etree.HTML(req.text)

    form_data = {i.attrib["name"]: i.attrib["value"] for i in root.xpath(
        "//input") if i.attrib["name"] != "ctl00$ButtonLogOut"}

    req = session.post(url=main_url, data=form_data)
    root = etree.HTML(req.text)

    form_data = {i.attrib.get("name"): i.attrib.get("value", "") for i in root.xpath("//input") if i.attrib["name"] not in [
        "ctl00$ButtonLogOut", 'ctl00$ContentPlaceHolder1$CK001$ButtonQuery', 'ctl00$ContentPlaceHolder1$CK001$ButtonClear', 'ctl00$ContentPlaceHolder1$CK001$ButtonPreview']}

    start_date = leave_data['days'][0]['day']
    end_date = leave_data['days'][-1]['day']
    form_data['ctl00$ContentPlaceHolder1$CK001$DateUCCBegin$text1'] = start_date
    form_data['ctl00$ContentPlaceHolder1$CK001$DateUCCEnd$text1'] = end_date
    req = session.post(url=main_url, data=form_data)
    root = etree.HTML(req.text)
    try:
        alert = root.xpath("//script[@language='javascript']")[0].text
        if alert.find('alert') >= 0:
            if alert.find('不在學期間') >= 0:  # 延遲請假也會用alert
                return error_code.LEAVE_SUBMIT_WRONG_DATE  # 日期不對//或是不再學期中
    except:
        pass

    global_form_data = {}
    global_form_data['ctl00$ContentPlaceHolder1$CK001$TextBoxReason'] = leave_data['reasonText']
    global_form_data['ctl00$ContentPlaceHolder1$CK001$ddlTeach'] = leave_data['teacherId']
    global_form_data['ctl00$ContentPlaceHolder1$CK001$RadioButtonListOption'] = leave_data['leaveType']
    time_code = root.xpath(
        "//div[@id='ContentPlaceHolder1_CK001_UpdatePanel2']//tr")
    if leave_data.get('delayReasonText', False) and req.text.find('延遲理由') > -1:
        global_form_data['ctl00$ContentPlaceHolder1$CK001$TextBoxDelayReason'] = leave_data.get(
            'delayReasonText', '')
    need_click_button_data = []
    # get need click button information
    for leave_day in leave_data['days']:
        for tr in time_code:
            _temp = tr.xpath('.//td')
            for index, value in enumerate(_temp[3:]):
                if leave_day['day'] == _temp[1].text:
                    if len(value.text) >= 40:
                        if index in leave_day['class']:
                            need_click_button_data.append(
                                value.xpath('.//input')[0].attrib.get("name", False))
    # set leave button data
    for click_data in need_click_button_data:
        form_data = {i.attrib.get("name"): i.attrib.get("value", "") for i in root.xpath(
            "//input") if i.attrib["name"][0:2] == "__"}
        form_data.update(global_form_data)
        form_data[click_data] = ""
        req = session.post(url=main_url, data=form_data)
        root = etree.HTML(req.text)

    # next step!
    form_data = {i.attrib.get("name"): i.attrib.get("value", "") for i in root.xpath(
        "//input") if i.attrib["name"][0:2] == "__"}
    form_data.update(global_form_data)

    if leave_data['leaveType'] in ['21', '44', '46']:
        # For wuhan virus. checkbox.
        form_data['ctl00$ContentPlaceHolder1$CK001$cbFlag'] = 'on'

    form_data['ctl00$ContentPlaceHolder1$CK001$ButtonCommit2'] = '下一步'
    req = session.post(url=main_url, data=form_data)
    root = etree.HTML(req.text)

    # delete defalut headers
    try:
        del session.headers['Content-Type']
    except:
        pass
    form_data = {i.attrib.get("name"): i.attrib.get("value", "") for i in root.xpath(
        "//input") if i.attrib["name"][0:2] == "__"}
    form_data['ctl00$ContentPlaceHolder1$CK001$ButtonSend'] = '存檔'

    # change to multipart request
    if proof_file != None:
        files = {'ctl00$ContentPlaceHolder1$CK001$FileUpload1': (
            proof_file_name, proof_file, 'image/%s' % proof_type)}
    else:
        files = {'ctl00$ContentPlaceHolder1$CK001$FileUpload1': (None, '')}

    req = session.post(url=main_url, data=form_data, files=files)
    root = etree.HTML(req.text)

    alert = root.xpath("//script[@language='javascript']")[0].text
    if alert.find('成功') >= 0:
        return error_code.LEAVE_SUBMIT_SUCCESS
    elif alert.find('假單請檢附附檔') >= 0:
        return error_code.LEAVE_SUBMIT_NEED_PROOF
    else:
        return error_code.LEAVE_SUBMIT_DATE_CONFLICT  # 重複請假
