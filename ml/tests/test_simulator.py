"""Tests for ml.simulator."""

import re
import numpy as np
import pandas as pd
import pytest

from ml.simulator import generate_dataset
from common.artifact_schema import ACCOUNT_ID_PATTERN


def test_generate_dataset_defaults_counts():
    """Verify default generation counts and typologies."""
    accounts_truth, txns = generate_dataset(n_accounts=3000, days=30, seed=42)

    assert len(accounts_truth) == 3000
    assert len(txns) > 5000

    fraud_accs = accounts_truth[accounts_truth["is_fraud"] == 1]
    assert len(fraud_accs) == 150

    typology_counts = fraud_accs["typology"].value_counts().to_dict()
    assert typology_counts.get("fan_in_fan_out") == 60
    assert typology_counts.get("pass_through_chain") == 48
    assert typology_counts.get("burst_velocity") == 42

    normal_accs = accounts_truth[accounts_truth["is_fraud"] == 0]
    assert len(normal_accs) == 2850
    assert (normal_accs["typology"] == "").all()
    assert (normal_accs["ring_id"] == "").all()


def test_generate_dataset_determinism():
    """Verify identical outputs for identical seeds."""
    accs1, txns1 = generate_dataset(n_accounts=500, days=10, seed=42)
    accs2, txns2 = generate_dataset(n_accounts=500, days=10, seed=42)

    pd.testing.assert_frame_equal(accs1, accs2)
    pd.testing.assert_frame_equal(txns1, txns2)

    # Different seed gives different result
    accs3, txns3 = generate_dataset(n_accounts=500, days=10, seed=99)
    assert not txns1["amount_inr"].equals(txns3["amount_inr"])


def test_generate_dataset_ids_and_references():
    """Verify unique IDs and foreign key integrity."""
    accounts_truth, txns = generate_dataset(n_accounts=1000, days=15, seed=42)

    # Account IDs
    assert accounts_truth["account_id"].is_unique
    for aid in accounts_truth["account_id"]:
        assert ACCOUNT_ID_PATTERN.match(aid)

    # Txn IDs
    assert txns["txn_id"].is_unique

    # Senders and receivers exist in accounts
    acc_set = set(accounts_truth["account_id"])
    assert set(txns["sender_id"]).issubset(acc_set)
    assert set(txns["receiver_id"]).issubset(acc_set)


def test_hard_negatives_present():
    """Verify hard negative account types (merchants, payroll, aggregators, night-active) are present in transactions."""
    accounts_truth, txns = generate_dataset(n_accounts=3000, days=30, seed=42)

    # Check night transactions among normal accounts
    normal_ids = set(accounts_truth[accounts_truth["is_fraud"] == 0]["account_id"])
    normal_out_txns = txns[txns["sender_id"].isin(normal_ids)].copy()
    normal_out_txns["hour"] = pd.to_datetime(normal_out_txns["timestamp"]).dt.hour
    night_txns = normal_out_txns[normal_out_txns["hour"].between(0, 4)]
    assert len(night_txns) > 0  # Hard negative for night ratio

    # Check fan-in merchants (normal accounts receiving from >= 20 distinct senders)
    normal_in_txns = txns[txns["receiver_id"].isin(normal_ids)]
    senders_per_normal = normal_in_txns.groupby("receiver_id")["sender_id"].nunique()
    merchants = senders_per_normal[senders_per_normal >= 20]
    assert len(merchants) > 0  # Hard negative for fan-in (merchants)


def test_quick_mode_scaling():
    """Verify quick mode with 1000 accounts scales and contains all typologies."""
    accounts_truth, txns = generate_dataset(n_accounts=1000, days=30, seed=42)
    assert len(accounts_truth) == 1000
    fraud_accs = accounts_truth[accounts_truth["is_fraud"] == 1]
    assert len(fraud_accs) in range(45, 55)

    typos = set(fraud_accs["typology"].unique())
    assert typos == {"fan_in_fan_out", "pass_through_chain", "burst_velocity"}
