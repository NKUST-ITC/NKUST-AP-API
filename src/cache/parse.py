from lxml import etree


def userinfo(html):

    root = etree.HTML(html)

    td = root.xpath("//td")
    if len(td) < 3:
        return False

    userData = {
        "educationSystem": td[3].text[5:],
        "department":  td[4].text[5:],
        "className": td[8].text[5:],
        "id": td[9].text[5:],
        "name": td[10].text[5:],
        "pictureUrl": "https://webap.nkust.edu.tw/nkust" +
        root.xpath("//img")[0].values()[0][2:]
    }
    return userData


def semesters(html):
    """return semesters json

    Args:
        html ([str]): ag_304_1 html

    Returns:
        [dict]: result
    """
    root = etree.HTML(html)

    data = {
        'data': [],
        'default': {
            'year': '',
            'value': '',
            'text': ''
        }
    }

    try:
        default_yms = root.xpath("id('yms_yms')/option[@selected]")[0]
        data['default']['year'] = default_yms.values()[0].split('#')[0]
        data['default']['value'] = default_yms.values()[0].split('#')[1]
        data['default']['text'] = default_yms.text
    except:
        pass
    try:
        options = map(lambda x: {"value": x.values()[0].split('#')[1],
                                 "year": x.values()[0].split('#')[0],
                                 "text": x.text},
                      root.xpath("id('yms_yms')/option")
                      )
    except:
        pass
    data['data'] = list(options)

    return data


def midterm_alert(html):
    root = etree.HTML(html)
    td = root.xpath("/html/body/form/table[1]//tr[@bgcolor='#FFFcee']//td")

    td = [w.text.replace('\xa0', '') for w in td]
    split_td = map(lambda x: td[int(x)-8: int(x)], range(8, len(td)+8, 8))
    raw_alert = map(lambda x: {'entry': x[0],
                               'className': x[1],
                               'title': x[2],
                               'group': x[3],
                               'instructors': x[4],
                               'reason': x[6],
                               'remark': x[7]
                               } if x[5] == "是" else None, split_td)
    mid_alert_list = [w for w in raw_alert if w != None]
    res = {
        "courses": mid_alert_list
    }
    return res


def scores(html):
    root = etree.HTML(html)

    td_etree = root.xpath("//tr[@bgcolor='#FFFcee']//td")

    raw_td = [td.text.replace('\xa0', '') for td in td_etree]

    split_td = map(lambda x: raw_td[int(
        x)-9: int(x)], range(9, len(raw_td)+9, 9))

    scores_list = [{
        'title': i[1],
        'units': i[2],
        'hours': i[3],
        'required': i[4],
        'at': i[5],
        'middleScore': i[6],
        'finalScore': i[7],
        "remark": i[8]
    } for i in split_td]

    total = root.xpath("//div[@align='left']")[0].text.split('　　　　')
    total = ["".join(i.split()) for i in total]

    detail = {
        "conduct": total[0][5::],
        "average": total[1][4::],
        "classRank": total[2][8::],
        "classPercentage": total[3][7:-1]
    }

    res = {
        "scores": scores_list,
        "detail": detail
    }

    return res


def coursetable(html):
    # <br> If veryyyy difficult to handle in lxml so.. replace it!
    html = html.replace('<br>', ',')

    result = {
        "courses": [],
        "coursetable": {
            "timeCodes": []
        }
    }

    root = etree.HTML(html)
    td = root.xpath('/html/body/form/table//font')
    corses_list = [x.text.replace('\xa0', '') for x in td][11::]
    # pylint: disable=unsubscriptable-object
    corses_list_split = map(lambda x: corses_list[int(
        x)-11: int(x)], range(11, len(corses_list)+11, 11))

    result_corses = [{"code": x[0],
                      "title": x[1],
                      "className": x[2],
                      "group": x[3],
                      "units": x[4],
                      "hours": x[5],
                      "required": x[6],
                      "at": x[7],
                      "times": x[8],
                      "location": {"room": x[10]}, "instructors": x[9].split(',')} for x in corses_list_split]

    course_table_xpath = root.xpath(
        '/html/body/table[@bordercolor="#999999"]//td[@bgcolor="#FFFcee"]')

    course_table = [corse.text.replace('\xa0', '')
                    for corse in course_table_xpath]

    # 2d arrary 7*15(days)
    corses_list = list(map(lambda x: course_table[int(
        x)-7: int(x)], range(7, len(course_table)+7, 7)))

    timecode_list_xpath = root.xpath(
        '/html/body/table[@bordercolor="#999999"]//td[@bgcolor="#ebebeb"]/font')

    week_name = ['Monday', 'Tuesday', 'Wednesday',
                 'Thursday', 'Friday', 'Saturday', 'Sunday']

    result['coursetable'].update({i: [] for i in week_name})

    date_list = []
    for i in timecode_list_xpath:
        temp = i.text.split(',')[1:3]
        result['coursetable']['timeCodes'].append(temp[0])
        cource_time_list = temp[1].split('-')
        start_time = cource_time_list[0][:2]+":"+cource_time_list[0][2:]
        end_time = cource_time_list[1][:2]+":"+cource_time_list[1][2:]
        date_list.append({
            'startTime': start_time,
            'endTime': end_time,
            'section': temp[0]
        })

    # 7 day for week
    for week_data_index, week_name_data in enumerate(week_name):
        for lession_index, lession_data in enumerate(corses_list):
            if lession_data[week_data_index]:
                course_split = lession_data[week_data_index].split(',')
                result['coursetable'][week_name_data].append({
                    'title': course_split[0],
                    'date': date_list[lession_index],
                    'location': {
                        'room': course_split[-2]
                    },
                    'instructors': course_split[1:-2]
                })

    result['courses'] = result_corses

    return result


def reward(html):
    html = html.replace('<br>', ',')

    result = {
        'data': []
    }

    root = etree.HTML(html)
    td = root.xpath('//tr[@bgcolor="#fffcee"]/td/font')

    reward_list = [x.text.replace('\xa0', '') for x in td]

    # pylint: disable=unsubscriptable-object
    reward_list_split = map(lambda x: reward_list[int(
        x)-6: int(x)], range(6, len(reward_list)+6, 6))

    result_data = [{"date": x[2],
                    "type": x[3],
                    "counts": x[4],
                    "reason": x[5]} for x in reward_list_split if x[4] != ""]

    result['data'] = result_data

    return result


def graduation(html):
    result = {
        "data": {
            "name": "",
            "className": "",
            "id": ""
        },
        "englishPass": "",
        "englishClassPass": ""
    }

    root = etree.HTML(html)
    pass_data = root.xpath('//div[@class="panel-body"]/span')
    if len(pass_data) < 2:
        return False
    result['englishPass'] = pass_data[0].text
    result['englishClassPass'] = pass_data[1].text

    user_data = root.xpath('//div[@class="panel-body"]/table/tr/td/span')
    if len(user_data) < 3:
        return False
    result['data']['name'] = user_data[2].text
    result['data']['className'] = user_data[0].text
    result['data']['id'] = user_data[1].text

    return result


def room_list(html):
    result = {
        "data": []
    }

    root = etree.HTML(html)
    room_list = [{'roomName': i.text,
                  'roomId': i.get('value')} for i in root.xpath(
        '//select[@name="room_id"]/option[@value!=""]')]
    result['data'] = room_list
    return result


def query_room(html):
    # <br> If veryyyy difficult to handle in lxml so.. replace it!
    html = html.replace('<br>', ',')

    result = {
        "courses": [],
        "coursetable": {
            "timeCodes": []
        }
    }

    root = etree.HTML(html)
    td = root.xpath('/html/body/form/table//font')
    corses_list = [x.text.replace('\xa0', '') for x in td][11::]
    # pylint: disable=unsubscriptable-object
    corses_list_split = map(lambda x: corses_list[int(
        x)-11: int(x)], range(11, len(corses_list)+11, 11))
    result_corses = [{"code": x[0],
                      "title": x[1],
                      "className": x[2],
                      "group": x[3],
                      "units": x[4],
                      "hours": x[5],
                      "required": x[7],
                      "at": x[8],
                      "times": x[9],
                      "instructors": x[10].split(',')} for x in corses_list_split]

    course_table_xpath = root.xpath(
        '/html/body/table[@bordercolor="#999999"]//td[@bgcolor="#fffcee"]//font')

    course_table = [corse.text.replace('\xa0', '')
                    for corse in course_table_xpath]

    # 2d arrary 7*15(days)
    corses_list = list(map(lambda x: course_table[int(
        x)-7: int(x)], range(7, len(course_table)+7, 7)))

    timecode_list_xpath = root.xpath(
        '/html/body/table[@bordercolor="#999999"]//td[@bgcolor="#ebebeb"]/font')

    week_name = ['Monday', 'Tuesday', 'Wednesday',
                 'Thursday', 'Friday', 'Saturday', 'Sunday']

    result['coursetable'].update({i: [] for i in week_name})

    date_list = []

    for i in timecode_list_xpath[7:]:
        temp = i.text.split(',')[1:3]
        result['coursetable']['timeCodes'].append(temp[0])
        cource_time_list = temp[1].split('-')
        start_time = cource_time_list[0][:2]+":"+cource_time_list[0][2:]
        end_time = cource_time_list[1][:2]+":"+cource_time_list[1][2:]
        date_list.append({
            'startTime': start_time,
            'endTime': end_time,
            'section': temp[0]
        })

    if len(corses_list) is not len(date_list):
        print('[Error] parser error on query empty room')  # for log

    for week_data_index, week_name_data in enumerate(week_name):
        for lession_index, lession_data in enumerate(corses_list):
            if lession_data[week_data_index]:
                course_split = lession_data[week_data_index].split(',')

                result['coursetable'][week_name_data].append({
                    'title': course_split[0],
                    'date': date_list[lession_index],
                    'instructors': course_split[1:-2]
                })

    result['courses'] = result_corses

    return result
