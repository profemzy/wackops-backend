from flask import Blueprint
from flask import jsonify
from flask import request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from ops.user.models import User
from ops.user.schemas import registration_schema
from ops.user.schemas import users_schema

user = Blueprint("user", __name__, url_prefix="/user")


# NOTE: This doesn't match the video since we don't want the registration
# page to require authentication. The @jwt_required decorator has been moved to
# only apply to the index function so we can send a POST to create a new user.
@user.before_request
def before_request():
    """We want all of these endpoints to be authenticated."""
    pass


@user.get("/")
@jwt_required()
def index():
    users = User.query.all()

    response = {"data": users_schema.dump(users)}

    return jsonify(response), 200


@user.post("")
def post():
    json_data = request.get_json()

    if not json_data:
        response = jsonify({"error": "Invalid input"})

        return response, 400

    try:
        data = registration_schema.load(json_data)
    except ValidationError as err:
        response = {"error": err.messages}

        return jsonify(response), 422

    new_user = User()
    new_user .email = data.get("email")
    new_user .username = data.get("username")
    new_user .password = User.encrypt_password(data.get("password"))

    new_user .save()

    return jsonify(data), 200
