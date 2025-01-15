import json
from unittest.mock import patch

import pytest
from flask import url_for

from ops.research.models import Research
from ops.user.models import User


@pytest.fixture
def user(session):
    # First check if user exists and delete if it does
    existing_user = (
        session.query(User).filter_by(email="test@example.com").first()
    )
    if existing_user:
        session.delete(existing_user)
        session.commit()

    user = User(username="test_user", email="test@example.com")
    user.password = user.encrypt_password("password101")
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def auth_headers(client, user):
    """Fixture to get authenticated headers"""
    response = client.post(
        url_for("api_v1.auth.post"),
        json={"identity": user.username, "password": "password101"},
    )
    token = response.json["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def research(session, user):
    research = Research(
        user_id=user.id,
        question="Howdy",
        answer="Howdy! How can I help you today",
    )
    session.add(research)
    session.commit()
    return research


def test_get_research_history(client, auth_headers, research, user):
    """Test getting research history for a user"""
    response = client.get(
        url_for("api_v1.researches.index") + f"?username={user.username}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert "data" in response.json
    assert len(response.json["data"]) == 1
    assert response.json["data"][0]["question"] == "Howdy"


def test_get_research_history_no_username(client, auth_headers):
    """Test getting research history without providing username"""
    response = client.get(
        url_for("api_v1.researches.index"), headers=auth_headers
    )

    assert response.status_code == 400
    assert response.json["error"]["message"] == "Username does not exist."


def test_get_research_history_invalid_user(client, auth_headers):
    """Test getting research history for non-existent user"""
    response = client.get(
        url_for("api_v1.researches.index") + "?username=nonexistent",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json["error"]["message"] == "Username does not exist."


def test_get_research_history_unauthorized(client):
    """Test getting research history without authentication"""
    response = client.get(
        url_for("api_v1.researches.index") + "?username=test"
    )
    assert response.status_code == 401


@patch("utils.openai.get_answer")
def test_create_research(mock_get_answer, client, auth_headers):
    """Test creating new research"""
    mock_response = {
        "choices": [
            {"message": {"content": "Howdy! How can I help you today."}}
        ]
    }
    mock_get_answer.return_value = json.dumps(mock_response)

    response = client.post(
        url_for("api_v1.researches.post"),
        headers=auth_headers,
        json={"question": "Howdy"},
    )

    assert response.status_code == 200
    assert "data" in response.json
    assert "id" in response.json["data"]
    assert "created_on" in response.json["data"]


def test_create_research_no_data(client, auth_headers):
    """Test creating research without providing data"""
    response = client.post(
        url_for("api_v1.researches.post"), headers=auth_headers, json={}
    )

    assert response.status_code == 400


def test_create_research_invalid_json(client, auth_headers):
    """Test creating research with invalid JSON"""
    response = client.post(
        url_for("api_v1.researches.post"),
        headers=auth_headers,
        json="invalid json",
    )

    assert response.status_code == 422


def test_create_research_unauthorized(client):
    """Test creating research without authentication"""
    response = client.post(
        url_for("api_v1.researches.post"), json={"question": "Howdy"}
    )
    assert response.status_code == 401
