import falcon
from auth import auth_middleware

# pylint: disable=invalid-name
app = falcon.API(middleware=[auth_middleware])
