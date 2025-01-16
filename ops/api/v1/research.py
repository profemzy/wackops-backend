import json
from http import HTTPStatus
from typing import Dict
from typing import Tuple
from typing import Union

from flasgger import swag_from
from flask import Blueprint
from flask import request
from flask_jwt_extended import current_user
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from lib.flask_pusher import pusher
from ops.research.models import Research
from ops.research.schemas import add_research_schema
from ops.research.schemas import researches_schema
from ops.user.models import User
from utils.openai import AzureOpenAIClient

researches = Blueprint("researches", __name__, url_prefix="/researches/")

# Swagger documentation
GET_RESEARCHES_DOCS = {
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
                                "example": "Username parameter is required.",
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

POST_RESEARCH_DOCS = {
    "tags": ["Research"],
    "summary": "Create new research question",
    "description": "Ask question to get AI-generated answer and save research",
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
                    "error": {
                        "type": "string",
                        "example": "Invalid request body",
                    }
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
        "500": {
            "description": "OpenAI API error",
            "schema": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "example": "Failed to get response from Azure OpenAI",
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


@researches.before_request
@jwt_required()
def before_request() -> None:
    """Require authentication for all endpoints in this blueprint."""
    pass


def create_error_response(message: str, status_code: int) -> Tuple[Dict, int]:
    """Create a standardized error response."""
    return {"error": {"message": message}}, status_code


def create_success_response(data: Union[Dict, list]) -> Tuple[Dict, int]:
    """Create a standardized success response."""
    return {"data": data}, HTTPStatus.OK


@researches.get("/")
@swag_from(GET_RESEARCHES_DOCS)
def index() -> Tuple[Dict, int]:
    """Get research history for a specific user."""
    username = request.args.get("username")

    if not username:
        return create_error_response(
            "Username parameter is required.", HTTPStatus.BAD_REQUEST
        )

    user = User.find_by_identity(username)
    if not user:
        return create_error_response(
            "Username does not exist.", HTTPStatus.NOT_FOUND
        )

    researches_query = Research.query.filter_by(user_id=user.id).order_by(
        Research.created_on.desc()
    )

    return create_success_response(researches_schema.dump(researches_query))


@researches.post("")
@swag_from(POST_RESEARCH_DOCS)
def post() -> Tuple[Dict, int]:
    """Create a new research entry with AI-generated answer."""
    json_data = request.get_json()
    if not json_data:
        return create_error_response(
            "Invalid request body", HTTPStatus.BAD_REQUEST
        )

    try:
        data = add_research_schema.load(json_data)
    except ValidationError as err:
        return create_error_response(
            err.messages, HTTPStatus.UNPROCESSABLE_ENTITY
        )

    client = AzureOpenAIClient()
    ai_response = client.get_answer(
        question=data["question"],
        context="AI assistant that explains technical concepts clearly.",
    )

    if not ai_response:
        return create_error_response(
            "Failed to get response from Azure OpenAI",
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    try:
        answer_content = ai_response["choices"][0]["message"]["content"]

        research = Research()
        research.user_id = current_user.id
        research.question = data["question"]
        research.answer = answer_content
        research.save()

        # Trigger Pusher notification
        pusher.trigger(
            "private-research",
            "new-research",
            {
                "question": research.question,
                "answer": research.answer,
                "username": current_user.username,
            },
        )

        response_data = {
            "created_on": research.created_on,
            "id": research.id,
            "question": research.question,
            "answer": research.answer,
        }

        return create_success_response(response_data)

    except (KeyError, json.JSONDecodeError) as e:
        return create_error_response(
            f"Error processing AI response: {str(e)}",
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )
