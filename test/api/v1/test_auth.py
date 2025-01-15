import pytest
from flask import url_for

from ops.user.models import User


@pytest.fixture
def user(session):
    # First check if user exists and delete if it does
    existing_user = (
        session.query(User).filter_by(email="demo@gmail.com").first()
    )
    if existing_user:
        session.delete(existing_user)
        session.commit()

    user = User(username="demo_user", email="demo@gmail.com")
    user.password = user.encrypt_password("password101")
    session.add(user)
    session.commit()
    return user


def test_login(client, user):
    response = client.post(
        url_for("api_v1.auth.post"),
        json={"identity": user.username, "password": "password101"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json["data"]


def test_login_invalid_credentials(client):
    response = client.post(
        url_for("api_v1.auth.post"),
        json={"identity": "wronguser", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json["error"]["message"] == "Invalid identity or password"


@pytest.fixture
def auth_headers(client, user):
    """Fixture to get authenticated headers"""
    response = client.post(
        url_for("api_v1.auth.post"),
        json={"identity": user.username, "password": "password101"},
    )
    assert (
        response.status_code == 200
    ), f"Login failed with response: {response.json}"
    token = response.json["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_logout(client, auth_headers):
    response = client.delete(
        url_for("api_v1.auth.delete"), headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json["data"]["logout"] is True


def test_pusher_auth(client, auth_headers):
    response = client.post(
        url_for("api_v1.auth.pusher"),
        data={"channel_name": "test_channel", "socket_id": "123.456"},
        headers=auth_headers,
    )
    assert response.status_code == 200
