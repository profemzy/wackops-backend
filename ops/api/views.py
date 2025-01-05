import json
from datetime import datetime
from http import HTTPStatus
from zoneinfo import ZoneInfo
from typing import Tuple
import logging
from functools import wraps
from utils.openai import get_answer

from flask import Blueprint, jsonify, request, Response

# Configure logging
logger = logging.getLogger(__name__)

api = Blueprint("api", __name__, url_prefix="/api")


def validate_json_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return (
                jsonify(
                    {
                        "error": "Unsupported Media Type",
                        "message": "Content-Type must be application/json",
                        "status_code": HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                    }
                ),
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
            )
        return f(*args, **kwargs)

    return decorated_function


@api.route("/")
def hello() -> Tuple[Response, int]:
    return jsonify({"message": "Hello from Flask!"}), HTTPStatus.OK


@api.route("/answer", methods=["POST"])
@validate_json_request
def answer() -> Tuple[Response, int]:
    try:
        data = request.json
        question = data.get("question", "").strip()
        context = data.get(
            "context",
            "You are an AI assistant that helps people find information..",
        ).strip()

        if not question:
            return (
                jsonify(
                    {
                        "error": "Bad Request",
                        "status_code": HTTPStatus.BAD_REQUEST,
                        "message": "Question is required",
                    }
                ),
                HTTPStatus.BAD_REQUEST,
            )

        logger.info(f"Processing question: {question[:100]}...")
        result = get_answer(question, context)

        # Parse the result if it's a JSON string
        try:
            if isinstance(result, str):
                parsed_result = json.loads(result)
                answer_content = parsed_result["choices"][0]["message"][
                    "content"
                ]
            else:
                answer_content = result

            logger.info("Successfully processed answer")
            return (
                jsonify(
                    {
                        "success": True,
                        "data": {
                            "answer": answer_content,
                            "processed_at": datetime.now(
                                ZoneInfo("UTC")
                            ).isoformat(),
                        },
                    }
                ),
                HTTPStatus.OK,
            )

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse AI response: {str(e)}")
            return (
                jsonify(
                    {
                        "success": True,
                        "data": {
                            "answer": result,
                            "processed_at": datetime.now(
                                ZoneInfo("UTC")
                            ).isoformat(),
                        },
                    }
                ),
                HTTPStatus.OK,
            )

    except Exception as e:
        logger.error(
            f"Unexpected error in answer endpoint: " f"{str(e)}", exc_info=True
        )
        return server_error()


@api.route("/health")
def health() -> Tuple[Response, int]:
    return (
        jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now(ZoneInfo("UTC")).isoformat(),
                "version": "1.0.0",  # Consider pulling from config or environment
            }
        ),
        HTTPStatus.OK,
    )


@api.errorhandler(404)
def not_found(error) -> Tuple[Response, int]:
    logger.warning(f"Resource not found: {error}")
    return (
        jsonify(
            {
                "error": "Resource not found",
                "status_code": HTTPStatus.NOT_FOUND,
                "message": str(error),
            }
        ),
        HTTPStatus.NOT_FOUND,
    )


@api.errorhandler(500)
def server_error(error=None) -> Tuple[Response, int]:
    error_message = str(error) if error else "An unexpected error occurred"
    logger.error(f"Internal server error: {error_message}")
    return (
        jsonify(
            {
                "error": "Internal server error",
                "status_code": HTTPStatus.INTERNAL_SERVER_ERROR,
                "message": "An unexpected error occurred",
            }
        ),
        HTTPStatus.INTERNAL_SERVER_ERROR,
    )
