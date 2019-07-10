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
