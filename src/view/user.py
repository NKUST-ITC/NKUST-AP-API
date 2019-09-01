import json
import datetime
import falcon

from auth import jwt_auth
from utils.util import webap_login_cache_required
from utils import config
from cache import ap_cache
from utils import error_code


class userInfo:

    @falcon.before(webap_login_cache_required)
    def on_get(self, req, resp):
        # jwt payload
        payload = req.context['user']['user']

        user_info = ap_cache.user_info(
            username=payload['username'])

        if isinstance(user_info, dict):
            resp.media = user_info
            resp.status = falcon.HTTP_200
            return True
        elif user_info == error_code.USER_INFO_PARSE_ERROR:
            # graduate
            user_info = ap_cache.graduate_user_info(
                username=payload['username'])
            if isinstance(user_info, str):
                resp.body = user_info
                resp.media = falcon.MEDIA_JSON
                resp.status = falcon.HTTP_200
                return True
            else:
                resp.status = falcon.HTTP_204
        raise falcon.HTTPInternalServerError(
            description='something error ?')


class userSemesters:

    def on_get(self, req, resp):

        semesters_data = ap_cache.semesters()
        if isinstance(semesters_data, str):
            resp.body = semesters_data
            resp.media = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
            return True
        # error handle
        elif isinstance(semesters_data, int):
            if semesters_data == error_code.SEMESTERS_QUERY_ERROR:
                resp.status = falcon.HTTP_500
                raise falcon.HTTPInternalServerError(
                    description="SEMESTERS QUERY ERROR")

            elif semesters_data == error_code.CACHE_WEBAP_ERROR:
                resp.status = falcon.HTTP_503
                raise falcon.HTTPServiceUnavailable()

        else:
            raise falcon.HTTPInternalServerError(
                description='something error ?')


class userMidtermAlerts:

    @falcon.before(webap_login_cache_required)
    def on_get(self, req, resp):
        # jwt payload
        payload = req.context['user']['user']
        if req.get_param('year') == None and req.get_param('semester') == None:
            raise falcon.HTTPBadRequest(description='params error')

        if len(req.get_param('year')) > 4 or len(req.get_param('semester')) > 2:
            raise falcon.HTTPBadRequest(description='params error')

        midterm_alerts_dict = ap_cache.midterm_alerts(
            username=payload['username'],
            year=req.get_param('year'), semester=req.get_param('semester'))

        if isinstance(midterm_alerts_dict, dict):
            resp.media = midterm_alerts_dict
            resp.status = falcon.HTTP_200
            return True
        elif midterm_alerts_dict == error_code.MIDTERM_ALERTS_PARSER_ERROR:
            resp.status = falcon.HTTP_204
            return False

        raise falcon.HTTPInternalServerError(
            description='something error ?')


class userScore:

    @falcon.before(webap_login_cache_required)
    def on_get(self, req, resp):
        # jwt payload
        payload = req.context['user']['user']
        if req.get_param('year') == None and req.get_param('semester') == None:
            raise falcon.HTTPBadRequest(description='params error')

        if len(req.get_param('year')) > 4 or len(req.get_param('semester')) > 2:
            raise falcon.HTTPBadRequest(description='params error')

        score_dict = ap_cache.score(
            username=payload['username'],
            year=req.get_param('year'), semester=req.get_param('semester'))

        if isinstance(score_dict, dict):
            resp.media = score_dict
            resp.status = falcon.HTTP_200
            return True
        elif score_dict == error_code.SCORES_PARSE_ERROR:
            # 204
            resp.status = falcon.HTTP_204
            return True
        raise falcon.HTTPInternalServerError(
            description='something error ?')


class userCourseTable:

    @falcon.before(webap_login_cache_required)
    def on_get(self, req, resp):
        # jwt payload
        payload = req.context['user']['user']
        if req.get_param('year') == None and req.get_param('semester') == None:
            raise falcon.HTTPBadRequest(description='params error')

        if len(req.get_param('year')) > 4 or len(req.get_param('semester')) > 2:
            raise falcon.HTTPBadRequest(description='params error')

        course_dict = ap_cache.coursetable(
            username=payload['username'],
            year=req.get_param('year'), semester=req.get_param('semester'))

        if isinstance(course_dict, str):
            resp.body = course_dict
            resp.media = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
            return True
        # error handle
        elif isinstance(course_dict, int):
            if course_dict == error_code.COURSETABLE_QUERY_ERROR:
                resp.status = falcon.HTTP_500
                raise falcon.HTTPInternalServerError(
                    description="COURSETABLE QUERY ERROR")
            elif course_dict == error_code.COURSETABLE_PARSE_ERROR:
                resp.status = falcon.HTTP_204
                return False

        raise falcon.HTTPInternalServerError(
            description='something error ?')


class userReward:

    @falcon.before(webap_login_cache_required)
    def on_get(self, req, resp):
        # jwt payload
        payload = req.context['user']['user']
        if req.get_param('year') == None and req.get_param('semester') == None:
            raise falcon.HTTPBadRequest(description='params error')

        if len(req.get_param('year')) > 4 or len(req.get_param('semester')) > 2:
            raise falcon.HTTPBadRequest(description='params error')

        reward_dict = ap_cache.reward(
            username=payload['username'],
            year=req.get_param('year'), semester=req.get_param('semester'))
        if isinstance(reward_dict, dict):
            resp.media = reward_dict
            resp.status = falcon.HTTP_200
            return True
        elif reward_dict == error_code.REWARD_PARSE_ERROR:
            resp.status = falcon.HTTP_204
            return False

        raise falcon.HTTPInternalServerError(
            description='something error ?')


class userGraduation:

    def on_get(self, req, resp):
        # jwt payload
        payload = req.context['user']['user']

        graduation_data = ap_cache.cache_graduation_threshold(
            username=payload['username'], password=payload['password'])

        if isinstance(graduation_data, str):
            resp.body = graduation_data
            resp.media = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
            return True
        # error handle
        elif isinstance(graduation_data, int):
            if graduation_data == error_code.GRADUATION_ERROR:
                resp.status = falcon.HTTP_500
                raise falcon.HTTPInternalServerError(
                    description="GRADUATION QUERY ERROR")

            elif graduation_data == error_code.CACHE_WEBAP_ERROR:
                resp.status = falcon.HTTP_503
                raise falcon.HTTPServiceUnavailable()

        else:
            raise falcon.HTTPInternalServerError(
                description='something error ?')


class userRoomList:

    def on_get(self, req, resp):

        if len(req.get_param('campus')) > 1:
            raise falcon.HTTPBadRequest(description='params error')
        if req.get_param('campus') not in ['1', '2', '3', '4', '5']:
            raise falcon.HTTPBadRequest(description='params error')

        campus_room_list_data = ap_cache.room_list(
            campus=req.get_param('campus'))

        if isinstance(campus_room_list_data, str):
            resp.body = campus_room_list_data
            resp.media = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
            return True
        # error handle
        elif isinstance(campus_room_list_data, int):
            if campus_room_list_data == error_code.ROOM_LIST_ERROR:
                resp.status = falcon.HTTP_500
                raise falcon.HTTPInternalServerError(
                    description="ROOM LIST QUERY ERROR")

            elif campus_room_list_data == error_code.CACHE_WEBAP_ERROR:
                resp.status = falcon.HTTP_503
                raise falcon.HTTPServiceUnavailable()

        else:
            raise falcon.HTTPInternalServerError(
                description='something error ?')


class userQueryEmptyRoom:

    def on_get(self, req, resp):

        if req.get_param('year') is None or req.get_param('semester') is None:
            raise falcon.HTTPBadRequest(description='params error')
        if len(req.get_param('year')) > 4 or len(req.get_param('semester')) > 2:
            raise falcon.HTTPBadRequest(description='params error')
        if req.get_param('roomid') is None:
            raise falcon.HTTPBadRequest(description='params error')

        empty_room_data = ap_cache.query_empty_room(
            room_id=req.get_param('roomid'), year=req.get_param('year'), semester=req.get_param('semester'))

        if isinstance(empty_room_data, str):
            resp.body = empty_room_data
            resp.media = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
            return True
        # error handle
        elif isinstance(empty_room_data, int):
            if empty_room_data == error_code.QUERY_EMPTY_ROOM_ERROR:
                resp.status = falcon.HTTP_500
                raise falcon.HTTPInternalServerError(
                    description="EMPTY ROOM QUERY ERROR")

            elif empty_room_data == error_code.CACHE_WEBAP_ERROR:
                resp.status = falcon.HTTP_503
                raise falcon.HTTPServiceUnavailable()

        raise falcon.HTTPInternalServerError(
            description='something error ?')
