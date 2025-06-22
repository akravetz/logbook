"""Simple tests for the FastAPI app without database dependency."""

from fastapi.testclient import TestClient

from workout_api.core.main import app


def test_app_creation():
    """Test that the FastAPI app can be created."""
    assert app is not None
    assert app.title == "Workout API"


def test_health_check_without_db():
    """Test health check endpoint without database."""
    # Create a simple client without database dependency
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "version" in data


def test_root_endpoint_without_db():
    """Test root endpoint without database."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "health" in data
