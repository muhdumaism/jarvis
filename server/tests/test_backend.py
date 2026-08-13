import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify uvicorn health check endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "jarvis",
        "version": "1.0.0"
    }


def test_auth_login_fail():
    """Verify wrong login credentials fail authorization with 401."""
    response = client.post(
        "/api/auth/login",
        json={"username": "wrong_user", "password": "wrong_password"}
    )
    assert response.status_code == 401
    assert "detail" in response.json()
