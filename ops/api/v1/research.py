import json

from flasgger import swag_from
from flask import Blueprint
from flask import jsonify
from flask import request
from flask_jwt_extended import current_user
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from lib.flask_pusher import pusher
from ops.research.models import Research
from ops.research.schemas import add_research_schema
from ops.research.schemas import research_schema
from ops.user.models import User
from utils.openai import get_answer

researches = Blueprint("researches", __name__, url_prefix="/researches/")


@researches.before_request
@jwt_required()
def before_request():
    """We want all of these endpoints to be authenticated."""
    pass


@researches.get("/")
@swag_from(
    {
        "tags": ["Research"],
        "summary": "Get user research history",
        "description": "Get all research questions and answers for a user",
        "security": [{"Bearer": []}],
        "parameters": [
            {
                "name": "username",
                "in": "query",
                "type": "string",
                "required": True,
                "description": "Username to fetch research history for",
                "example": "john_doe",
            }
        ],
        "responses": {
            "200": {
                "description": "Research history retrieved successfully",
                "schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer", "example": 1},
                                    "question": {
                                        "type": "string",
                                        "example": "What is machine learning?",
                                    },
                                    "answer": {
                                        "type": "string",
                                        "example": "Explain Machine learning",
                                    },
                                    "created_on": {
                                        "type": "string",
                                        "format": "date-time",
                                        "example": "2025-01-14T18:39:03Z",
                                    },
                                },
                            },
                        }
                    },
                },
            },
            "400": {
                "description": "Missing username parameter",
                "schema": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "example": "Username does not exist.",
                                }
                            },
                        }
                    },
                },
            },
            "401": {"description": "Unauthorized - Valid JWT token required"},
            "404": {
                "description": "User not found",
                "schema": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "example": "Username does not exist.",
                                }
                            },
                        }
                    },
                },
            },
        },
    }
)
def index():
    response = {"error": {"message": "Username does not exist."}}

    username = request.args.get("username", default=None)

    if username is None:
        return jsonify(response), 400

    user = User.find_by_identity(username)

    if user is None:
        return jsonify(response), 404

    all_researches = Research.query.filter_by(user_id=user.id).order_by(
        Research.created_on.desc()
    )

    response = {"data": research_schema.dump(all_researches)}

    return jsonify(response), 200


@researches.post("")
@swag_from(
    {
        "tags": ["Research"],
        "summary": "Create new research question",
        "description": "Ask question to get AI-generated answer,save research",
        "security": [{"Bearer": []}],
        "parameters": [
            {
                "name": "body",
                "in": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "example": "What is machine learning?",
                            "description": "Research question to be answered",
                        }
                    },
                    "required": ["question"],
                },
            }
        ],
        "responses": {
            "200": {
                "description": "Research created successfully",
                "schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer", "example": 1},
                                "question": {
                                    "type": "string",
                                    "example": "What is machine learning?",
                                },
                                "answer": {
                                    "type": "string",
                                    "example": "Explain Machine learning",
                                },
                                "created_on": {
                                    "type": "string",
                                    "format": "date-time",
                                    "example": "2025-01-14T18:39:03Z",
                                },
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
            "401": {"description": "Unauthorized - Valid JWT token required"},
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
        "x-webhook": {
            "name": "Pusher Event",
            "url": "private-research",
            "event": "new-research",
            "description": "Notification sent when new research is created",
            "payload": {
                "question": "string",
                "answer": "string",
                "username": "string",
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
        data = add_research_schema.load(json_data)
    except ValidationError as err:
        response = {"error": err.messages}
        return jsonify(response), 422

    context = "You are an AI assistant that helps people find information.."
    result = get_answer(data["question"], context)

    parsed_result = json.loads(result)
    answer_content = parsed_result["choices"][0]["message"]["content"]

    research = Research()
    research.user_id = current_user.id
    research.question = data["question"]
    research.answer = answer_content
    research.save()

    pusher.trigger(
        "private-research",
        "new-research",
        {
            "question": research.question,
            "answer": research.answer,
            "username": current_user.username,
        },
    )

    response = {
        "data": {
            "created_on": research.created_on,
            "id": research.id,
            "question": research.question,
            "answer": research.answer,
        }
    }

    return jsonify(response), 200
