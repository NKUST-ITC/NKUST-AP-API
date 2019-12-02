from utils.leave_tool import teacher_list
import json
if __name__ == "__main__":
    campus_list = [
        {'id': 1, "campus_name": '建工校區'},
        {'id': 2, "campus_name": '燕巢校區'},
        {'id': 3, "campus_name": '第一校區'},
        {'id': 4, "campus_name": '楠梓校區'},
        {'id': 5, "campus_name": '旗津校區'}
    ]
    data = {'data': []}
    username = input('NKUST account : ')
    password = input('NKUST password : ')
    for i in campus_list:
        _temp_ = {
            "campusName": i['campus_name'],
            "department": None
        }
        res = teacher_list(
            username=username,
            password=password,
            campus_id=i['id']
        )
        _temp_['department'] = res
        data['data'].append(_temp_)
    open('res.json', 'w').write(json.dumps(data))
