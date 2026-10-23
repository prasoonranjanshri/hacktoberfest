"""Tests for ml.features."""

import numpy as np
import pandas as pd
import pytest

from common.artifact_schema import FEATURE_COLUMNS
from ml.features import build_features


def test_build_features_hand_computed():
    """Verify all 14 features against exact hand-computed values on a tiny dataset."""
    accounts_truth = pd.DataFrame(
        [
            {
                "account_id": "ACC-00001",
                "account_age_days": 50.0,
                "is_fraud": 0,
                "typology": "",
                "ring_id": "",
            },
            {
                "account_id": "ACC-00002",
                "account_age_days": 100.0,
                "is_fraud": 0,
                "typology": "",
                "ring_id": "",
            },
            {
                "account_id": "ACC-00003",
                "account_age_days": 200.0,
                "is_fraud": 0,
                "typology": "",
                "ring_id": "",
            },
            {
                "account_id": "ACC-00004",
                "account_age_days": 300.0,
                "is_fraud": 0,
                "typology": "",
                "ring_id": "",
            },
            {
                "account_id": "ACC-00005",
                "account_age_days": 400.0,
                "is_fraud": 0,
                "typology": "",
                "ring_id": "",
            },
        ]
    )

    transactions = pd.DataFrame(
        [
            # ACC-00001 incoming
            {
                "txn_id": "T1",
                "timestamp": "2026-09-01T10:00:00",
                "sender_id": "ACC-00003",
                "receiver_id": "ACC-00001",
                "amount_inr": 1000.0,
                "typology": "",
            },
            {
                "txn_id": "T2",
                "timestamp": "2026-09-01T12:00:00",
                "sender_id": "ACC-00002",
                "receiver_id": "ACC-00001",
                "amount_inr": 2000.0,
                "typology": "",
            },
            # ACC-00001 outgoing
            {
                "txn_id": "T3",
                "timestamp": "2026-09-01T10:05:00",
                "sender_id": "ACC-00001",
                "receiver_id": "ACC-00002",
                "amount_inr": 800.0,
                "typology": "",
            },
            {
                "txn_id": "T4",
                "timestamp": "2026-09-01T10:08:00",
                "sender_id": "ACC-00001",
                "receiver_id": "ACC-00004",
                "amount_inr": 400.0,
                "typology": "",
            },
            {
                "txn_id": "T5",
                "timestamp": "2026-09-02T02:00:00",
                "sender_id": "ACC-00001",
                "receiver_id": "ACC-00002",
                "amount_inr": 500.0,
                "typology": "",
            },
        ]
    )

    features = build_features(transactions, accounts_truth)

    # Check columns
    assert list(features.columns) == FEATURE_COLUMNS
    assert list(features.index) == list(accounts_truth["account_id"])

    # Test ACC-00001 hand-calculated values
    row1 = features.loc["ACC-00001"]
    assert row1["txn_count_out"] == 3.0
    assert row1["txn_count_in"] == 2.0
    assert row1["total_out_inr"] == 1700.0
    assert row1["total_in_inr"] == 3000.0
    assert pytest.approx(row1["avg_amount_out"], 0.01) == 1700.0 / 3.0
    assert pytest.approx(row1["night_txn_ratio"], 0.01) == 1.0 / 3.0
    assert pytest.approx(row1["new_payee_ratio"], 0.01) == 2.0 / 3.0
    assert row1["max_out_txns_10min"] == 2.0
    assert row1["account_age_days"] == 50.0
    assert row1["n_unique_senders"] == 2.0
    assert row1["n_unique_receivers"] == 2.0
    assert pytest.approx(row1["forward_ratio_15min"], 0.01) == 1200.0 / 3000.0
    assert pytest.approx(row1["median_hold_minutes"], 0.01) == 422.5

    # Check edge cases
    # ACC-00003: no incoming transactions
    row3 = features.loc["ACC-00003"]
    assert row3["txn_count_in"] == 0.0
    assert row3["total_in_inr"] == 0.0
    assert row3["n_unique_senders"] == 0.0
    assert row3["forward_ratio_15min"] == 0.0
    assert row3["median_hold_minutes"] == 1440.0

    # ACC-00004: no outgoing transactions
    row4 = features.loc["ACC-00004"]
    assert row4["txn_count_out"] == 0.0
    assert row4["total_out_inr"] == 0.0
    assert row4["avg_amount_out"] == 0.0
    assert row4["night_txn_ratio"] == 0.0
    assert row4["new_payee_ratio"] == 0.0
    assert row4["max_out_txns_10min"] == 0.0
    assert row4["n_unique_receivers"] == 0.0

    # ACC-00005: isolated account
    row5 = features.loc["ACC-00005"]
    assert row5["txn_count_out"] == 0.0
    assert row5["txn_count_in"] == 0.0
    assert row5["median_hold_minutes"] == 1440.0
    assert row5["neighbour_mean_forward_ratio"] == 0.0


def test_build_features_full_dataset_speed():
    """Verify feature building on 3000 accounts runs in well under a minute."""
    import time
    from ml.simulator import generate_dataset

    accounts_truth, txns = generate_dataset(n_accounts=3000, days=30, seed=42)
    start_time = time.time()
    features = build_features(txns, accounts_truth)
    elapsed = time.time() - start_time

    assert len(features) == 3000
    assert list(features.columns) == FEATURE_COLUMNS
    assert not features.isna().any().any()
    assert elapsed < 30.0  # Must be well under 60s
