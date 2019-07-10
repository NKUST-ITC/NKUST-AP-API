import falcon
from auth import auth_middleware
from view import api
from view import user
# pylint: disable=invalid-name
app = falcon.API(middleware=[auth_middleware])

app.add_route('/oauth/token', api.ApiLogin())
app.add_route('/user/info', user.userInfo())
