"""Tests for authentication endpoints."""

from fastapi.testclient import TestClient


REGISTER_PAYLOAD = {
    "tenant_name": "Test Corp",
    "full_name": "Test Admin",
    "email": "admin@testcorp.com",
    "password": "SecurePass123!",
}


def test_register_creates_tenant_and_user(client: TestClient) -> None:
    """POST /auth/register should return 201 with user data."""
    response = client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["email"] == "admin@testcorp.com"
    assert data["data"]["role"] == "admin"


def test_register_password_too_weak(client: TestClient) -> None:
    """POST /auth/register should reject passwords without uppercase or digit."""
    payload = {**REGISTER_PAYLOAD, "email": "weak@test.com", "password": "weakpassword"}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_register_invalid_email(client: TestClient) -> None:
    """POST /auth/register should reject malformed email addresses."""
    payload = {**REGISTER_PAYLOAD, "email": "not-an-email"}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_login_with_valid_credentials(client: TestClient) -> None:
    """POST /auth/login should return access_token and refresh_token."""
    # Register first
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    # Login with form data (OAuth2 password flow)
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_wrong_password(client: TestClient) -> None:
    """POST /auth/login should return 401 for wrong password."""
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": REGISTER_PAYLOAD["email"],
            "password": "WrongPassword999!",
        },
    )
    assert response.status_code == 401


def test_get_me_requires_auth(client: TestClient) -> None:
    """GET /auth/me should return 401 without a Bearer token."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_with_valid_token(client: TestClient) -> None:
    """GET /auth/me should return user profile when authenticated."""
    # Register + login
    client.post("/api/v1/auth/register", json={
        **REGISTER_PAYLOAD,
        "email": "me-test@testcorp.com",
    })
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "me-test@testcorp.com", "password": REGISTER_PAYLOAD["password"]},
    )
    token = login_resp.json()["access_token"]

    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "me-test@testcorp.com"


def test_refresh_token(client: TestClient) -> None:
    """POST /auth/refresh should return a new access token."""
    client.post("/api/v1/auth/register", json={
        **REGISTER_PAYLOAD,
        "email": "refresh-test@testcorp.com",
    })
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "refresh-test@testcorp.com", "password": REGISTER_PAYLOAD["password"]},
    )
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()
