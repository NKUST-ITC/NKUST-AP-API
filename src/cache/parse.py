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
