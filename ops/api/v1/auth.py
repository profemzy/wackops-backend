from flask import Blueprint
from flask import jsonify
from flask import request
from flask_jwt_extended import create_access_token
from flask_jwt_extended import current_user
from flask_jwt_extended import jwt_required
from flask_jwt_extended import set_access_cookies
from flask_jwt_extended import unset_jwt_cookies
from marshmallow import ValidationError

from lib.flask_pusher import pusher as _pusher
from ops.user.models import User
from ops.user.schemas import auth_schema

auth = Blueprint("auth", __name__, url_prefix="/")


@auth.post("")
def post():
    json_data = request.get_json()

    if not json_data:
        response = {"error": "Invalid input"}

        return jsonify(response), 400

    try:
        data = auth_schema.load(json_data)
    except ValidationError as err:
        response = {"error": err.messages}

        return jsonify(response), 422

    user = User.find_by_identity(data["identity"])

    if user and user.authenticated(password=data["password"]):
        access_token = create_access_token(identity=user.username)

        response = jsonify({"data": {"access_token": access_token}})

        # Set the JWTs and the CSRF double submit protection cookies.
        set_access_cookies(response, access_token)

        return response, 200

    response = jsonify({"error": {"message": "Invalid identity or password"}})

    return response, 401


@auth.delete("")
@jwt_required()
def delete():
    response = jsonify({"data": {"logout": True}})

    # Because the JWTs are stored in an httponly cookie now, we cannot
    # log the user out by simply deleting the cookie in the frontend.
    # We need the backend to send us a response to delete the cookies
    # in order to logout. unset_jwt_cookies is a helper function to
    # do just that.
    unset_jwt_cookies(response)

    return response, 200


@auth.post("pusher")
@jwt_required()
def pusher():
    if not request.form:
        response = {"error": "Invalid input"}

        return jsonify(response), 400

    response = _pusher.authenticate(
        channel=request.form["channel_name"],
        socket_id=request.form["socket_id"],
        # Pusher requires a user_id, it's how you can identify a user.
        custom_data={"user_id": current_user.username},
    )

    return jsonify(response), 200
