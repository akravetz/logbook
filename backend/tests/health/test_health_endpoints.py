"""Tests for health check endpoints."""

from fastapi.testclient import TestClient


def test_simple_health_check(client: TestClient):
    """Test simple health check endpoint."""
    response = client.get("/health/")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "version" in data
    assert data["version"] == "1.0.0"


def test_database_health_check(client: TestClient):
    """Test database health check endpoint."""
    response = client.get("/health/db")
    assert response.status_code == 200

    data = response.json()
    # Database might be healthy or unhealthy depending on test setup
    assert data["status"] in ["healthy", "unhealthy"]
    assert data["database"] in ["connected", "disconnected"]

    if data["status"] == "healthy":
        assert "response_time_ms" in data
        assert isinstance(data["response_time_ms"], int | float)
        assert data["response_time_ms"] >= 0
    else:
        # For unhealthy state, response_time_ms should be None
        assert data.get("response_time_ms") is None


def test_full_health_check(client: TestClient):
    """Test comprehensive health check endpoint."""
    response = client.get("/health/full")
    assert response.status_code == 200

    data = response.json()

    # Check app health (should always be healthy)
    assert "app" in data
    app_health = data["app"]
    assert app_health["status"] == "healthy"
    assert "environment" in app_health
    assert "version" in app_health

    # Check database health (may vary based on test setup)
    assert "database" in data
    db_health = data["database"]
    assert db_health["status"] in ["healthy", "unhealthy"]
    assert db_health["database"] in ["connected", "disconnected"]


def test_health_endpoint_backward_compatibility(client: TestClient):
    """Test that /health still works as expected (backward compatibility)."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "version" in data
