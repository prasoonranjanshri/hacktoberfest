"""Tests for /api/alerts and /api/budget-curve endpoints."""

from pathlib import Path
from fastapi.testclient import TestClient
import pandas as pd
import pytest

from backend.app.config import ARTIFACTS_DIR
from backend.app.errors import INVALID_BUDGET, VALIDATION_ERROR
from common.metrics import budget_metrics


def test_alerts_ordering_and_summary(client: TestClient):
    """Verify alert ranking, tie-breaking, and budget_summary against accounts.csv."""
    accounts_csv = Path(ARTIFACTS_DIR) / "accounts.csv"
    df = pd.read_csv(accounts_csv, dtype={"account_id": str, "typology": str, "ring_id": str})

    budget = 100
    response = client.get(f"/api/alerts?budget={budget}")
    assert response.status_code == 200
    data = response.json()

    assert data["budget"] == budget
    bs = data["budget_summary"]
    alerts = data["alerts"]
    assert len(alerts) == budget

    # Hand-calculate expected ranking
    items = []
    for row in df.itertuples():
        items.append((float(getattr(row, "risk_score")), getattr(row, "account_id"), getattr(row, "is_fraud")))
    items.sort(key=lambda x: (-x[0], x[1]))

    expected_top = items[:budget]
    for i, alert in enumerate(alerts):
        exp_score, exp_aid, exp_fraud = expected_top[i]
        assert alert["rank"] == i + 1
        assert alert["account_id"] == exp_aid
        assert pytest.approx(alert["risk_score"], 0.0001) == exp_score
        assert alert["ground_truth_fraud"] == bool(exp_fraud == 1)
        assert isinstance(alert["top_reason"], str)

    # Hand-calculate expected budget_summary
    bm_full = budget_metrics(df["is_fraud"], df["risk_score"], budget=budget, account_ids=df["account_id"])
    bm_beh = budget_metrics(df["is_fraud"], df["baseline_score"], budget=budget, account_ids=df["account_id"])

    assert bs["alerts_returned"] == bm_full["alerts_returned"]
    assert bs["true_frauds_caught"] == bm_full["true_frauds_caught"]
    assert bs["false_alerts"] == bm_full["false_alerts"]
    assert bs["total_frauds"] == int(df["is_fraud"].sum())
    assert pytest.approx(bs["recall"], 0.0001) == bm_full["recall"]
    assert pytest.approx(bs["precision"], 0.0001) == bm_full["precision"]
    assert bs["behaviour_only_true_frauds_caught"] == bm_beh["true_frauds_caught"]
    expected_fa_per_1000 = round(bm_full["false_alerts"] / len(df) * 1000.0, 4)
    assert pytest.approx(bs["false_alerts_per_1000_accounts"], 0.0001) == expected_fa_per_1000


def test_alerts_invalid_budget(client: TestClient):
    """Verify specific error codes for invalid budgets."""
    # budget = 0 -> INVALID_BUDGET 422
    r0 = client.get("/api/alerts?budget=0")
    assert r0.status_code == 422
    assert r0.json()["error"]["code"] == INVALID_BUDGET

    # budget = 1001 -> INVALID_BUDGET 422
    r1001 = client.get("/api/alerts?budget=1001")
    assert r1001.status_code == 422
    assert r1001.json()["error"]["code"] == INVALID_BUDGET

    # budget = abc -> VALIDATION_ERROR 422
    r_abc = client.get("/api/alerts?budget=abc")
    assert r_abc.status_code == 422
    assert r_abc.json()["error"]["code"] == VALIDATION_ERROR


def test_budget_curve_endpoint(client: TestClient):
    """Verify /api/budget-curve response structure and monotonic behaviour."""
    accounts_csv = Path(ARTIFACTS_DIR) / "accounts.csv"
    df = pd.read_csv(accounts_csv)

    response = client.get("/api/budget-curve")
    assert response.status_code == 200
    data = response.json()

    assert data["total_accounts"] == len(df)
    assert data["total_frauds"] == int(df["is_fraud"].sum())

    budgets = data["budgets"]
    assert budgets == list(range(10, 310, 10))

    full = data["full"]
    beh = data["behaviour_only"]

    assert len(full["true_frauds_caught"]) == len(budgets)
    assert len(full["false_alerts"]) == len(budgets)
    assert len(full["recall"]) == len(budgets)

    # Monotonic non-decreasing true_frauds_caught
    for i in range(1, len(budgets)):
        assert full["true_frauds_caught"][i] >= full["true_frauds_caught"][i - 1]
        assert beh["true_frauds_caught"][i] >= beh["true_frauds_caught"][i - 1]
