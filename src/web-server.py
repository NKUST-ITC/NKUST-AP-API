import falcon
from auth import auth_middleware
from view import api
from view import user
from view import bus
from view import news
# pylint: disable=invalid-name
app = falcon.API(middleware=[auth_middleware])

app.add_route('/oauth/token', api.ApiLogin())
app.add_route('/oauth/token/all', api.DeleteAllToken())
app.add_route('/user/info', user.userInfo())
app.add_route('/user/scores', user.userScore())
app.add_route('/user/semesters', user.userSemesters())
app.add_route('/user/midterm-alerts', user.userMidtermAlerts())
app.add_route('/user/coursetable', user.userCourseTable())
app.add_route('/user/reward-and-penalty', user.userReward())
# app.add_route('/user/graduation-threshold', user.userGraduation())
app.add_route('/user/room/list', user.userRoomList())
app.add_route('/user/empty-room/info', user.userQueryEmptyRoom())
app.add_route('/bus/reservations', bus.busUserReservations())
app.add_route('/server/info', api.ServerStatus())
app.add_route('/bus/timetables', bus.busTimeTable())
app.add_route('/news/school', news.acadNews())