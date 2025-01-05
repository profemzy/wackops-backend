from flask import Blueprint
from flask import jsonify
from datetime import datetime
from zoneinfo import ZoneInfo
from http import HTTPStatus

api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/")
def hello():
    return jsonify({"message": "Hello from Flask!"})


@api.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(ZoneInfo("UTC")).isoformat()
    })


@api.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Resource not found",
        "status_code": HTTPStatus.NOT_FOUND,
        "message": str(error)
    }), HTTPStatus.NOT_FOUND


@api.errorhandler(500)
def server_error():
    return jsonify({
        "error": "Internal server error",
        "status_code": HTTPStatus.INTERNAL_SERVER_ERROR,
        "message": "An unexpected error occurred"
    }), HTTPStatus.INTERNAL_SERVER_ERROR
