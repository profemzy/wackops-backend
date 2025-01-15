from flask_debugtoolbar import DebugToolbarExtension
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_static_digest import FlaskStaticDigest
from flasgger import Swagger

debug_toolbar = DebugToolbarExtension()
jwt = JWTManager()
db = SQLAlchemy()
marshmallow = Marshmallow()
flask_static_digest = FlaskStaticDigest()
swagger = Swagger()
