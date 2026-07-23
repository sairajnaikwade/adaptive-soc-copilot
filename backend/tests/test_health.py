"""Tests for GET /api/v1/health endpoint."""

from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    """Health endpoint must return HTTP 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_response_structure(client: TestClient) -> None:
    """Health response must contain required fields."""
    response = client.get("/api/v1/health")
    data = response.json()

    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "app_name" in data


def test_root_returns_welcome(client: TestClient) -> None:
    """Root endpoint returns welcome message with docs link."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "docs" in data
    assert "health" in data
