from flask import Blueprint

from ops.api.v1.auth import auth
from ops.api.v1.research import researches
from ops.api.v1.user import user

api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")

api_v1.register_blueprint(auth)
api_v1.register_blueprint(user)
api_v1.register_blueprint(researches)
