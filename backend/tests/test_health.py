"""Tests for GET /api/health and error handling."""

from pathlib import Path
import tempfile
from fastapi.testclient import TestClient
from backend.app.errors import ARTIFACTS_NOT_FOUND, NOT_FOUND
from backend.app.main import app
from backend.app.store import ArtifactStore, get_store
import backend.app.store as store_module


def test_health_success(client: TestClient):
    """GET /api/health returns the contract JSON on the synthetic pipeline artifacts."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "mulenet-api"
    assert data["version"] == "1.0.0"
    assert data["artifacts_loaded"] is True
    assert data["data_source"] == "synthetic_pipeline"
    assert data["generated_at"] is not None


def test_unknown_route_returns_404_envelope(client: TestClient):
    """Unknown route returns standard error envelope with 404 NOT_FOUND."""
    response = client.get("/api/non-existent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == NOT_FOUND
    assert "message" in data["error"]
    assert "details" in data["error"]


def test_summary_success(client: TestClient):
    """GET /api/summary returns dataset and model metrics matching real artifacts."""
    response = client.get("/api/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["data_source"] == "synthetic_pipeline"
    assert data["dataset"]["n_accounts"] == 3000
    assert data["dataset"]["n_fraud_accounts"] == 150
    assert data["dataset"]["fraud_rate"] == 0.05
    assert "typology_counts" in data["dataset"]
    assert data["model"]["name"] == "xgboost"
    assert data["model"]["cv_scheme"] == "GroupKFold"
    assert "pr_auc" in data["model"]
    assert "pr_auc_behaviour_only" in data["model"]


def test_drift_unavailable_by_default(client: TestClient):
    """GET /api/drift returns available: false when drift.json is absent."""
    response = client.get("/api/drift")
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is False


def test_missing_artifacts_returns_503(client: TestClient, monkeypatch):
    """Data endpoints return 503 ARTIFACTS_NOT_FOUND when artifacts are not loaded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_store = ArtifactStore(artifacts_dir=Path(tmpdir))
        assert fake_store.loaded is False

        # Patch _store_instance and get_store to return fake unloaded store
        monkeypatch.setattr(store_module, "_store_instance", fake_store)
        monkeypatch.setattr("backend.app.routes.health.get_store", lambda: fake_store)

        # Health should still return 200 with artifacts_loaded = False
        health_resp = client.get("/api/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["artifacts_loaded"] is False

        # Summary should return 503 ARTIFACTS_NOT_FOUND
        summary_resp = client.get("/api/summary")
        assert summary_resp.status_code == 503
        err = summary_resp.json()["error"]
        assert err["code"] == ARTIFACTS_NOT_FOUND

        # Alerts should return 503 ARTIFACTS_NOT_FOUND
        alerts_resp = client.get("/api/alerts")
        assert alerts_resp.status_code == 503
        assert alerts_resp.json()["error"]["code"] == ARTIFACTS_NOT_FOUND
