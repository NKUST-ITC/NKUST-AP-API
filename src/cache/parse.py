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

    res = {
        "scores": scores_list
    }

    return res
