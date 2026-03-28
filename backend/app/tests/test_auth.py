from __future__ import annotations


def test_signup_login_and_current_user(client) -> None:
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "operator@example.com",
            "username": "operator",
            "password": "secret123",
        },
    )
    assert signup_response.status_code == 201
    signup_payload = signup_response.json()
    assert signup_payload["email"] == "operator@example.com"
    assert signup_payload["token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {signup_payload['token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "operator"

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "operator@example.com",
            "password": "secret123",
        },
    )
    assert login_response.status_code == 200
    assert login_response.json()["token"]


def test_signup_rejects_duplicate_email(client) -> None:
    payload = {
        "email": "duplicate@example.com",
        "username": "duplicate-one",
        "password": "secret123",
    }
    assert client.post("/api/v1/auth/signup", json=payload).status_code == 201

    duplicate_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "duplicate@example.com",
            "username": "duplicate-two",
            "password": "secret123",
        },
    )
    assert duplicate_response.status_code == 409


def test_me_requires_valid_bearer_token(client) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
