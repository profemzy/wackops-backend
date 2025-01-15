from flasgger import swag_from
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
@swag_from(
    {
        "tags": ["Authentication"],
        "summary": "Authenticate user and obtain access token",
        "description": "User login, returns JWT token on successful login.",
        "parameters": [
            {
                "name": "credentials",
                "in": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "identity": {
                            "type": "string",
                            "description": "Username or email",
                        },
                        "password": {
                            "type": "string",
                            "description": "User password",
                        },
                    },
                    "required": ["identity", "password"],
                },
            }
        ],
        "responses": {
            "200": {
                "description": "Login successful",
                "schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "object",
                            "properties": {
                                "access_token": {
                                    "type": "string",
                                    "description": "JWT access token",
                                }
                            },
                        }
                    },
                },
            },
            "400": {
                "description": "Invalid request body",
                "schema": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string", "example": "Invalid input"}
                    },
                },
            },
            "401": {
                "description": "Authentication failed",
                "schema": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "example": "Invalid identity or password",
                                }
                            },
                        }
                    },
                },
            },
            "422": {
                "description": "Validation error",
                "schema": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "description": "Validation error messages",
                        }
                    },
                },
            },
        },
    }
)
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
        set_access_cookies(response, access_token)
        return response, 200

    response = jsonify({"error": {"message": "Invalid identity or password"}})
    return response, 401


@auth.delete("")
@jwt_required()
@swag_from(
    {
        "tags": ["Authentication"],
        "summary": "Logout current user",
        "description": "Invalidates current JWT token,removes related cookies",
        "security": [{"Bearer": []}],
        "responses": {
            "200": {
                "description": "Successfully logged out",
                "schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "object",
                            "properties": {
                                "logout": {"type": "boolean", "example": True}
                            },
                        }
                    },
                },
            },
            "401": {
                "description": "Unauthorized - valid JWT token required",
                "schema": {
                    "type": "object",
                    "properties": {
                        "msg": {
                            "type": "string",
                            "example": "Missing JWT token",
                        }
                    },
                },
            },
        },
    }
)
def delete():
    response = jsonify({"data": {"logout": True}})
    unset_jwt_cookies(response)
    return response, 200


@auth.post("pusher")
@jwt_required()
@swag_from(
    {
        "tags": ["Authentication"],
        "summary": "Authenticate Pusher connection",
        "description": "Authenticates Pusher connection for real-time updates",
        "security": [{"Bearer": []}],
        "parameters": [
            {
                "name": "channel_name",
                "in": "formData",
                "required": True,
                "type": "string",
                "description": "Name of the Pusher channel",
            },
            {
                "name": "socket_id",
                "in": "formData",
                "required": True,
                "type": "string",
                "description": "Socket ID for the Pusher connection",
            },
        ],
        "responses": {
            "200": {
                "description": "Successfully authenticated Pusher connection",
                "schema": {
                    "type": "object",
                    "description": "Pusher authentication response",
                },
            },
            "400": {
                "description": "Invalid request data",
                "schema": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string", "example": "Invalid input"}
                    },
                },
            },
            "401": {
                "description": "Unauthorized - valid JWT token required",
                "schema": {
                    "type": "object",
                    "properties": {
                        "msg": {
                            "type": "string",
                            "example": "Missing JWT token",
                        }
                    },
                },
            },
        },
    }
)
def pusher():
    if not request.form:
        response = {"error": "Invalid input"}
        return jsonify(response), 400

    response = _pusher.authenticate(
        channel=request.form["channel_name"],
        socket_id=request.form["socket_id"],
        custom_data={"user_id": current_user.username},
    )

    return jsonify(response), 200
