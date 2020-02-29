from lxml import etree
import requests
import re
from utils import error_code
from utils import config

ACAD_URL = 'https://acad.nkust.edu.tw/app/index.php?Action=mobilercglist'


def acad(page=0):
    """acad news crawler.

    Args:
        page (int, optional): [description]. Defaults to 0.

    Returns:
        [list]: success
        [int]: ACAD_ERROR
               ACAD_TIMEOUT
    """
    data = {
        'Rcg': 232,
        'Op': 'getpartlist',
        'Page': page
    }
    try:
        req = requests.post(url=ACAD_URL, data=data,
                            timeout=config.ACAD_TIMEOUT)
    except requests.exceptions.ConnectTimeout as e:
        return error_code.ACAD_TIMEOUT

    if req.status_code == 200:
        req = req.json()['content']
        root = etree.HTML(req)
        node = root.xpath('//*[@class="d-txt"]')
        date = [node[i] for i in range(0, len(node), 3)]
        href = root.xpath('//*[@class="d-txt"]//a')

        base_id = page*15

        notification = [{
            'link': href_data.attrib['href'],
            'info':{
                'id': base_id+index,
                'title': href_data.attrib['title'],
                'date': re.search("([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))", date_time.text).group()
            }
        } for index, (date_time, href_data) in enumerate(zip(date, href))]
        return notification
    return error_code.ACAD_ERROR
