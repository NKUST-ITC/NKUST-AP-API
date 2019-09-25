import requests
from bs4 import BeautifulSoup
import json
from utils import config, error_code
from crawler import leave_crawler


def teacher_list(username, password, campus_id):

    session = requests.session()
    login_status = leave_crawler.login(session, username, password)
    if login_status != error_code.LEAVE_LOGIN_SUCCESS:
        print('login fail.')
        return False

    main_url = 'http://leave.nkust.edu.tw/CK001MainM.aspx'
    req = session.get(main_url)
    soup = BeautifulSoup(req.text, 'html.parser')
    sp = soup.find_all('input')
    form_data = {i.get('name'): i.get('value')
                 for i in sp if i.get('name') != "ctl00$ButtonLogOut"}

    req = session.post(url=main_url, data=form_data)
    soup = BeautifulSoup(req.text, 'html.parser')
    sp = soup.find_all('input')
    form_data = {i.get('name'): i.get('value')
                 for i in sp if i.get('name') not in ["ctl00$ButtonLogOut", 'ctl00$ContentPlaceHolder1$CK001$ButtonQuery', 'ctl00$ContentPlaceHolder1$CK001$ButtonClear', 'ctl00$ContentPlaceHolder1$CK001$ButtonPreview']}
    fake_date = '108/09/21'
    form_data['ctl00$ContentPlaceHolder1$CK001$DateUCCEnd$text1'] = fake_date
    form_data['ctl00$ContentPlaceHolder1$CK001$DateUCCBegin$text1'] = fake_date

    req = session.post(url=main_url, data=form_data)
    soup = BeautifulSoup(req.text, 'html.parser')
    sp = soup.find_all('input')

    form_data = {i.get('name'): i.get('value')
                 for i in sp[:4] if i.get('name') != "ctl00$ButtonLogOut"}

    form_data['__EVENTTARGET'] = 'ctl00$ContentPlaceHolder1$CK001$ddlCmpArea'
    form_data['ctl00$ContentPlaceHolder1$CK001$ddlCmpArea'] = campus_id
    form_data['ctl00$ContentPlaceHolder1$CK001$TextBoxReason'] = ''
    form_data['ctl00$ContentPlaceHolder1$CK001$ddlUnitE'] = ''
    form_data['ctl00$ContentPlaceHolder1$CK001$ddlTeach'] = ''
    req = session.post(url=main_url, data=form_data)
    soup = BeautifulSoup(req.text, 'html.parser')

    place_list = soup.find(
        id='ContentPlaceHolder1_CK001_ddlUnitE').find_all('option')[1:]
    place_list = {i.get('value'): i.text for i in place_list}
    result = []
    for k, v in place_list.items():
        _temp = {
            'departmentName': v,
            "teacherList": []
        }
        sp = soup.find_all('input')
        form_data = {i.get('name'): i.get('value')
                     for i in sp[:4] if i.get('name') != "ctl00$ButtonLogOut"}

        form_data['__EVENTTARGET'] = 'ctl00$ContentPlaceHolder1$CK001$ddlUnitE'
        form_data['ctl00$ContentPlaceHolder1$CK001$ddlCmpArea'] = campus_id
        form_data['ctl00$ContentPlaceHolder1$CK001$TextBoxReason'] = ''
        form_data['ctl00$ContentPlaceHolder1$CK001$ddlUnitE'] = k
        form_data['ctl00$ContentPlaceHolder1$CK001$ddlTeach'] = ''
        req = session.post(url=main_url, data=form_data)

        soupt = BeautifulSoup(req.text, 'html.parser')

        teacher_list = soupt.find(
            id='ContentPlaceHolder1_CK001_ddlTeach').find_all('option')[1:]
        _temp_list = [{
            "teacherName": i.text,
            "teacherId": i.get('value')
        } for i in teacher_list]
        _temp['teacherList'] = _temp_list
        result.append(_temp)

    return result


if __name__ == "__main__":
    campus_list = [
        {'id': 1, "campus_name": '建工校區'},
        {'id': 2, "campus_name": '燕巢校區'},
        {'id': 3, "campus_name": '第一校區'},
        {'id': 4, "campus_name": '楠梓校區'},
        {'id': 5, "campus_name": '旗津校區'}
    ]
    data = {'data': []}
    for i in campus_list:
        _temp_ = {
            "campusName": i['campus_name'],
            "department": None
        }
        res = teacher_list(
            username=input('NKUST account : '),
            password=input('NKUST password : '),
            campus_id=i['id']
        )
        _temp_['department'] = res
        data['data'].append(_temp_)
    open('res.json', 'w').write(json.dumps(data))
