"""Tests for /api/accounts/{account_id}/graph endpoint."""

from pathlib import Path
from fastapi.testclient import TestClient
import pandas as pd
import pytest

from backend.app.config import ARTIFACTS_DIR
from backend.app.errors import (
    ACCOUNT_NOT_FOUND,
    INVALID_HOPS,
    INVALID_MAX_NODES,
)


def test_graph_structure_and_constraints(client: TestClient):
    """Verify ego-network graph structure, center inclusion, and edge constraints."""
    accounts_csv = Path(ARTIFACTS_DIR) / "accounts.csv"
    df_accs = pd.read_csv(accounts_csv)

    # Pick top risk account
    top_aid = df_accs.sort_values(by="risk_score", ascending=False).iloc[0]["account_id"]

    response = client.get(f"/api/accounts/{top_aid}/graph?hops=1&max_nodes=40")
    assert response.status_code == 200
    data = response.json()

    assert data["center_id"] == top_aid
    assert data["hops"] == 1
    assert isinstance(data["truncated"], bool)

    nodes = data["nodes"]
    edges = data["edges"]

    # 1. Center node is present and marked is_center
    node_ids = {n["id"] for n in nodes}
    assert top_aid in node_ids
    center_node = next(n for n in nodes if n["id"] == top_aid)
    assert center_node["is_center"] is True

    # Other nodes must have is_center=False
    for n in nodes:
        if n["id"] != top_aid:
            assert n["is_center"] is False

    # 2. Edges only exist between included nodes
    for e in edges:
        assert e["source"] in node_ids
        assert e["target"] in node_ids
        assert e["txn_count"] >= 1
        assert e["total_amount_inr"] > 0
        assert "first_ts" in e
        assert "last_ts" in e


def test_graph_truncation_small_max_nodes(client: TestClient):
    """Verify truncation occurs when max_nodes is smaller than candidate counterparties."""
    accounts_csv = Path(ARTIFACTS_DIR) / "accounts.csv"
    txns_csv = Path(ARTIFACTS_DIR) / "transactions.csv"
    df_txns = pd.read_csv(txns_csv)

    # Find an account with many counterparties (e.g. >= 10)
    senders = df_txns.groupby("receiver_id")["sender_id"].nunique()
    busy_aid = senders.sort_values(ascending=False).index[0]

    response = client.get(f"/api/accounts/{busy_aid}/graph?hops=1&max_nodes=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 5
    assert data["truncated"] is True


def test_graph_hops_two(client: TestClient):
    """Verify hops=2 returns valid 2-hop ego network."""
    accounts_csv = Path(ARTIFACTS_DIR) / "accounts.csv"
    df_accs = pd.read_csv(accounts_csv)
    top_aid = df_accs.sort_values(by="risk_score", ascending=False).iloc[0]["account_id"]

    resp1 = client.get(f"/api/accounts/{top_aid}/graph?hops=1&max_nodes=40")
    resp2 = client.get(f"/api/accounts/{top_aid}/graph?hops=2&max_nodes=40")

    assert resp1.status_code == 200
    assert resp2.status_code == 200

    data1 = resp1.json()
    data2 = resp2.json()

    assert data2["hops"] == 2
    # 2 hops should have at least as many nodes as 1 hop
    assert len(data2["nodes"]) >= len(data1["nodes"])


def test_graph_invalid_params(client: TestClient):
    """Verify specific error codes for invalid hops and max_nodes."""
    accounts_csv = Path(ARTIFACTS_DIR) / "accounts.csv"
    df_accs = pd.read_csv(accounts_csv)
    aid = df_accs.iloc[0]["account_id"]

    # hops = 0 -> INVALID_HOPS 422
    r_h0 = client.get(f"/api/accounts/{aid}/graph?hops=0")
    assert r_h0.status_code == 422
    assert r_h0.json()["error"]["code"] == INVALID_HOPS

    # hops = 3 -> INVALID_HOPS 422
    r_h3 = client.get(f"/api/accounts/{aid}/graph?hops=3")
    assert r_h3.status_code == 422
    assert r_h3.json()["error"]["code"] == INVALID_HOPS

    # max_nodes = 4 -> INVALID_MAX_NODES 422
    r_mn4 = client.get(f"/api/accounts/{aid}/graph?max_nodes=4")
    assert r_mn4.status_code == 422
    assert r_mn4.json()["error"]["code"] == INVALID_MAX_NODES

    # max_nodes = 101 -> INVALID_MAX_NODES 422
    r_mn101 = client.get(f"/api/accounts/{aid}/graph?max_nodes=101")
    assert r_mn101.status_code == 422
    assert r_mn101.json()["error"]["code"] == INVALID_MAX_NODES

    # Unknown account -> ACCOUNT_NOT_FOUND 404
    r_unknown = client.get("/api/accounts/ACC-99999/graph")
    assert r_unknown.status_code == 404
    assert r_unknown.json()["error"]["code"] == ACCOUNT_NOT_FOUND
