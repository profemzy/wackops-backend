from flasgger import swag_from
from flask import Blueprint
from flask import jsonify
from flask import request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from ops.user.models import User
from ops.user.schemas import registration_schema
from ops.user.schemas import users_schema

user = Blueprint("user", __name__, url_prefix="/user")


@user.before_request
def before_request():
    """We want all of these endpoints to be authenticated."""
    pass


@user.get("/")
@jwt_required()
@swag_from(
    {
        "tags": ["Users"],
        "summary": "Get all users",
        "description": "Returns all users. Requires authentication.",
        "security": [{"Bearer": []}],
        "responses": {
            "200": {
                "description": "List of users retrieved successfully",
                "schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer", "example": 1},
                                    "username": {
                                        "type": "string",
                                        "example": "john_doe",
                                    },
                                    "email": {
                                        "type": "string",
                                        "example": "john@example.com",
                                    },
                                },
                            },
                        }
                    },
                },
            },
            "401": {
                "description": "Unauthorized - Valid JWT token required",
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
def index():
    users = User.query.all()
    response = {"data": users_schema.dump(users)}
    return jsonify(response), 200


@user.post("")
@swag_from(
    {
        "tags": ["Users"],
        "summary": "Register new user",
        "description": "Creates a new user account.",
        "parameters": [
            {
                "name": "body",
                "in": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "format": "email",
                            "example": "user@example.com",
                            "description": "User's email address",
                        },
                        "username": {
                            "type": "string",
                            "example": "john_doe",
                            "description": "Unique username",
                        },
                        "password": {
                            "type": "string",
                            "format": "password",
                            "example": "secure_password123",
                            "description": "User's password",
                        },
                    },
                    "required": ["email", "username", "password"],
                },
            }
        ],
        "responses": {
            "200": {
                "description": "User successfully registered",
                "schema": {
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "example": "user@example.com",
                        },
                        "username": {"type": "string", "example": "john_doe"},
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
            "422": {
                "description": "Validation error",
                "schema": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "description": "Validation error messages",
                            "example": {
                                "email": ["Not a valid email address"],
                                "username": ["Username already exists"],
                            },
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
        response = jsonify({"error": "Invalid input"})
        return response, 400

    try:
        data = registration_schema.load(json_data)
    except ValidationError as err:
        response = {"error": err.messages}
        return jsonify(response), 422

    new_user = User()
    new_user.email = data.get("email")
    new_user.username = data.get("username")
    new_user.password = User.encrypt_password(data.get("password"))

    new_user.save()

    return jsonify(data), 200
