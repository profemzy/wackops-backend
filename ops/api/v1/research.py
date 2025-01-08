import json
from flask import Blueprint
from flask import request
from flask import jsonify
from flask_jwt_extended import jwt_required
from flask_jwt_extended import current_user
from marshmallow import ValidationError
from ops.user.models import User
from utils.openai import get_answer
from lib.flask_pusher import pusher
from ops.research.models import Research

from ops.research.schemas import research_schema, add_research_schema

researches = Blueprint("researches", __name__, url_prefix="/researches/")


@researches.before_request
@jwt_required()
def before_request():
    """We want all of these endpoints to be authenticated."""
    pass

@researches.get("/")
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
    answer_content = parsed_result["choices"][0]["message"][
        "content"
    ]

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
            "answer": research.answer
        }
    }

    return jsonify(response), 200
