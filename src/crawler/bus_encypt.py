import hashlib
import json
import re


def md5(data):
    md5_obj = hashlib.md5()
    md5_obj.update(data.encode('utf-8'))
    return md5_obj.hexdigest()


def str_find_last_index(content, target_string):
    if target_string is None:
        return -1
    index = -1
    res = 0
    while res != -1:
        res = content.find(target_string, res)
        if res != -1:
            index = res
            res += 1
    return index


class enc_function:
    def __init__(self, js_code):

        _temp = self.encA1_js_parser(js_code)
        self.seed = _temp['seed']
        self.seed_at = _temp['at_where']

    def encA1_js_parser(self, js_code):
        # http://bus.kuas.edu.tw/API/Scripts/a1
        seed_from_first_regex = re.compile(r"encA2\('((\d|\w){0,32})'")
        seed_from_last_regex = re.compile(
            r"encA2\(e(\w|\d|\s|\W){0,3}'((\d|\w){0,32})'\)")
        f_match = seed_from_first_regex.findall(js_code)
        l_match = seed_from_last_regex.findall(js_code)

        first_value = None
        last_value = None
        if len(f_match) > 0:
            first_value = f_match[-1][0]
        if len(l_match) > 0:
            last_value = l_match[-1][1]
        if str_find_last_index(js_code, first_value) > str_find_last_index(js_code, last_value):
            return {
                "seed": first_value,
                "at_where": "First"
            }

        return {"seed": last_value, "at_where": "Last"}

    def encA1(self, data):
        # Only use last encrypt seed, other command just let us confuse.
        if self.seed_at == 'Last':
            return md5(data+self.seed)
        return md5(self.seed+data)

    def encrypt(self, username: str, password: str):

        # Just random value
        # g = int(1163531501*random.uniform(0, 1))+15441
        # i = int(1163531502*random.uniform(0, 1))+0
        # j = int(1163531502*random.uniform(0, 1))+0
        # k = int(1163531502*random.uniform(0, 1))+0
        g = 419191959
        i = 930672927
        j = 1088434686
        k = 260123741

        g = md5("J"+str(g))
        i = md5("E"+str(i))
        j = md5("R"+str(j))
        k = md5("Y"+str(k))
        username = md5(username+self.encA1(g))
        password = md5(username+password+"JERRY"+self.encA1(i))

        l = md5(username+password+"KUAS"+self.encA1(j))
        l = md5(l + username+self.encA1("ITALAB")+self.encA1(k))
        l = md5(l + password+"MIS"+k)

        return json.dumps({
            "a": l,
            "b": g,
            "c": i,
            "d": j,
            "e": k,
            "f": password
        })
