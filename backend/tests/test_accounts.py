"""Tests for /api/accounts/{account_id} endpoint."""

from pathlib import Path
from fastapi.testclient import TestClient
import pandas as pd
import pytest

from backend.app.config import ARTIFACTS_DIR
from backend.app.errors import ACCOUNT_NOT_FOUND
from common.artifact_schema import FEATURE_COLUMNS


def test_account_detail_and_rank_consistency(client: TestClient):
    """Verify account details, all 14 features, and rank consistency with /api/alerts."""
    accounts_csv = Path(ARTIFACTS_DIR) / "accounts.csv"
    df = pd.read_csv(accounts_csv, dtype={"account_id": str, "typology": str, "ring_id": str})

    # Fetch top 10 alerts
    alerts_resp = client.get("/api/alerts?budget=10")
    assert alerts_resp.status_code == 200
    top_alerts = alerts_resp.json()["alerts"]

    # Check the top alert
    top_aid = top_alerts[0]["account_id"]
    top_resp = client.get(f"/api/accounts/{top_aid}")
    assert top_resp.status_code == 200
    top_data = top_resp.json()

    assert top_data["account_id"] == top_aid
    assert top_data["rank"] == 1
    assert pytest.approx(top_data["risk_score"], 0.0001) == top_alerts[0]["risk_score"]
    assert top_data["ground_truth_fraud"] == top_alerts[0]["ground_truth_fraud"]
    assert isinstance(top_data["reasons"], list)

    # Check 14 features
    assert set(top_data["features"].keys()) == set(FEATURE_COLUMNS)

    # Check rank consistency for the 5th alert
    fifth_aid = top_alerts[4]["account_id"]
    fifth_resp = client.get(f"/api/accounts/{fifth_aid}")
    assert fifth_resp.status_code == 200
    assert fifth_resp.json()["rank"] == 5


def test_account_detail_not_found(client: TestClient):
    """Unknown account_id returns 404 ACCOUNT_NOT_FOUND error envelope."""
    response = client.get("/api/accounts/ACC-99999")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == ACCOUNT_NOT_FOUND
    assert "ACC-99999" in data["error"]["message"]
