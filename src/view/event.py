# coding=utf-8
import json
from urllib.parse import parse_qs, urlparse

import falcon

from event.event_cache import coviddefense_info_and_send
from event.event_error_code import coviddefenseError, error
from utils.util import max_body, webap_login_cache_required


class event_QR:

    @falcon.before(max_body(64 * 1024))  # 64KB limit.
    @falcon.before(webap_login_cache_required)
    # covidefense server can't login without seat_id.
    def on_post(self, req, resp):
        jwt_payload = req.context['user']['user']
        if req.get_header('Content-Type') != None:
            if req.get_header('Content-Type').find('application/json') > -1:
                req_json = json.loads(
                    req.bounded_stream.read(), encoding='utf-8')
            elif req.get_header('Content-Type').find('www-form') > -1:
                req_body = req.stream.read()
                req_json = {}
                for k, v in parse_qs(req_body.decode('utf-8')).items():
                    if len(v) > 0:
                        req_json[k] = v[0]
        # basic check
        for key in req_json.keys():
            if key not in ['data', 'bus_id']:
                # return status code 406  not acceptable
                raise falcon.HTTPNotAcceptable(falcon.HTTP_NOT_ACCEPTABLE)

        # check request url
        send = False
        if '/event/send' in urlparse(req.url).path:
            # use urlparse to avoid query string bypass
            send = True

        # check event url
        event = urlparse(req_json['data'])

        if event.hostname == 'coviddefense.nkust.edu.tw' \
                and event.path == '/accessControl/seatLogin'\
                and event.query.find('seat=') > -1:

            try:
                seat_id = parse_qs(event.query, max_num_fields=1)['seat'][0]
            except ValueError as e:
                raise falcon.HTTPBadRequest(
                    description='query parameter too many.')
            if req_json.get('bus_id'):
                bus_id = req_json.get('bus_id')
            else:
                bus_id = ""

            req_status = coviddefense_info_and_send(
                account=jwt_payload['username'],
                password=jwt_payload['password'],
                seat_id=seat_id,
                bus_id=bus_id,
                send_confirm=send
            )

            error_json = {
                'code': 500,
                'description': ""
            }
            if isinstance(req_status, dict):
                resp.body = json.dumps(req_status, ensure_ascii='utf-8')
                resp.media = falcon.MEDIA_JSON
                resp.status = falcon.HTTP_200
                return True
            elif isinstance(req_status, coviddefenseError):
                if req_status == error.not_found_seat:
                    error_json['description'] = "座位錯誤"
                elif req_status == error.wrong_account_or_password:
                    error_json['description'] = "帳號密碼錯誤 (異常)\n(麻煩回報粉絲團)"
                elif req_status == error.something_error:
                    error_json['description'] = "異常錯誤"
                resp.body = json.dumps(error_json, ensure_ascii='utf-8')
                resp.media = falcon.MEDIA_JSON
                resp.status = falcon.HTTP_500
                return True

        raise falcon.HTTPInternalServerError(
            description='main something error.')
