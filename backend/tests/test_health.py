"""Tests for GET /api/health and error handling."""

from fastapi.testclient import TestClient


def test_health_success(client: TestClient):
    """GET /api/health returns the contract JSON on the sample artifacts."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "mulenet-api"
    assert data["version"] == "1.0.0"
    assert data["artifacts_loaded"] is True
    assert data["data_source"] == "sample_fixture"
    assert data["generated_at"] is not None


def test_unknown_route_returns_404_envelope(client: TestClient):
    """Unknown route returns standard error envelope with 404 NOT_FOUND."""
    response = client.get("/api/non-existent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "message" in data["error"]
    assert "details" in data["error"]
