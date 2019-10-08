import json
import datetime
import falcon
import sys

from auth import jwt_auth
from utils.util import leave_login_cache_required, max_body
from utils import config, error_code
from cache import leave_cache
# if this library is no longer maintained, change falcon(future), or cgi.
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import ValueTarget


class leave_list:

    @falcon.before(leave_login_cache_required)
    def on_get(self, req, resp):
        # jwt payload
        payload = req.context['user']['user']
        if req.get_param('year') == None and req.get_param('semester') == None:
            raise falcon.HTTPBadRequest(description='params error')

        if len(req.get_param('year')) > 4 or len(req.get_param('semester')) > 2:
            raise falcon.HTTPBadRequest(description='params error')

        leave_dict = leave_cache.get_leave_list(
            username=payload['username'],
            year=req.get_param('year'), semester=req.get_param('semester'))

        if isinstance(leave_dict, str):
            resp.body = leave_dict
            resp.media = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
            return True
        raise falcon.HTTPInternalServerError(
            description='something error ?')


class leave_submit_info:

    @falcon.before(leave_login_cache_required)
    def on_get(self, req, resp):
        # jwt payload
        payload = req.context['user']['user']

        submit_info = leave_cache.get_submit_info(username=payload['username'])

        if isinstance(submit_info, str):
            resp.body = submit_info
            resp.media = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
            return True
        if isinstance(submit_info, int):
            if submit_info == error_code.LEAVE_SUBMIT_INFO_GRADUATE_ERROR:
                raise falcon.HTTPForbidden(
                    description="400, graduate can't use this feature ", code=400)
        raise falcon.HTTPInternalServerError(
            description='something error ?')


class leave_submit:

    @falcon.before(leave_login_cache_required)
    @falcon.before(max_body(1024*1024*4))
    def on_post(self, req, resp):
        payload = req.context['user']['user']
        if req.get_header('Content-Type') != None:
            if req.get_header('Content-Type')[0:19] != 'multipart/form-data':
                raise falcon.HTTPBadRequest(code=400,
                                            description='wrong Content-Type, only support multipart/form-data ')
        else:
            raise falcon.HTTPBadRequest(
                code=406,
                description='not found Content-Type. ')

        def convert_lowercase_mutlipart(req_bytes_data):
            # cobert lower case MIME to defalut MIME type,Support cgi
            data = {
                'content-disposition': 'Content-Disposition',
                'content-type': 'Content-Type'
            }
            for k, v in data.items():
                req_bytes_data = req_bytes_data.replace(
                    bytes(k, encoding='utf-8'), bytes(v, encoding='utf-8'))
            return req_bytes_data

        parser = StreamingFormDataParser(headers=req.headers)
        leave_data_bytes = ValueTarget()
        parser.register('leavesData', leave_data_bytes)
        # save in memory don't do anything to it !
        leave_proof_image_bytes = ValueTarget()
        parser.register('proofImage', leave_proof_image_bytes)
        # load request
        parser.data_received(convert_lowercase_mutlipart(req.stream.read()))
        # check data
        if leave_proof_image_bytes != None:
            if (leave_proof_image_bytes.multipart_filename[-3:] not in ['png', 'jpg', 'PNG', "JPG"]) and (leave_proof_image_bytes.multipart_filename[-4:] not in ["jpeg", "JPEG"]):
                raise falcon.HTTPBadRequest(
                    code=401,
                    description='file type not support')
            if sys.getsizeof(leave_proof_image_bytes.value) > config.LEAVE_PROOF_IMAGE_SIZE_LIMIT:
                raise falcon.HTTPBadRequest(
                    code=402,
                    description='file size over limit.')
        try:
            leave_data = json.loads(
                leave_data_bytes.value.decode('utf-8'))
        except json.decoder.JSONDecodeError:
            raise falcon.HTTPBadRequest(
                code=403,
                description='leavesData JSONDecodeError ')
        submit_status = leave_cache.submit_leave(
            username=payload['username'],
            leave_data=leave_data,
            leave_proof=leave_proof_image_bytes)
        if isinstance(submit_status, bool):
            if submit_status is True:
                resp.status = falcon.HTTP_200
                return True
        elif isinstance(submit_status, int):
            if submit_status == error_code.LEAVE_SUBMIT_WRONG_DATE:
                raise falcon.HTTPForbidden(
                    code=410, description="leave date not accept.")
            elif submit_status == error_code.LEAVE_SUBMIT_NEED_PROOF:
                raise falcon.HTTPForbidden(
                    code=411, description='need proof image')
            elif submit_status == error_code.LEAVE_SUBMIT_DATE_CONFLICT:
                raise falcon.HTTPForbidden(
                    code=412, description='request leave date, is already submitted.')
            elif submit_status == error_code.LEAVE_SUBMIT_SOMETHING_ERROR:
                pass
        raise falcon.HTTPInternalServerError()
