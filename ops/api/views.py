from flask import Blueprint, jsonify

from config.settings import DEBUG

api = Blueprint("api", __name__, url_prefix="/api")

@api.route('/')
def hello():
    return jsonify({"message": "Hello from Flask!"})

@api.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@api.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500