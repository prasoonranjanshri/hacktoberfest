"""Tests for ml.explain."""

import pandas as pd
import pytest

from common.artifact_schema import FEATURE_COLUMNS
from ml.explain import TEMPLATES, build_reasons


def test_templates_cover_all_14_features():
    """Verify that TEMPLATES has an entry for all 14 FEATURE_COLUMNS."""
    assert set(TEMPLATES.keys()) == set(FEATURE_COLUMNS)
    assert len(TEMPLATES) == 14


def test_build_reasons_ordering_filtering_formatting():
    """Verify positive filtering, descending SHAP order, top_k truncation, and formatting."""
    accounts = ["ACC-00001", "ACC-00002", "ACC-00003"]
    
    # ACC-00001 has 4 positive shap values
    # ACC-00002 has all negative / zero shap values
    # ACC-00003 has 1 positive shap value
    features_df = pd.DataFrame(
        {
            "n_unique_senders": [15.0, 1.0, 2.0],
            "n_unique_receivers": [1.0, 1.0, 1.0],
            "forward_ratio_15min": [0.92, 0.0, 0.0],
            "median_hold_minutes": [6.5, 1440.0, 720.0],
            "neighbour_mean_forward_ratio": [0.05, 0.0, 0.0],
            "max_out_txns_10min": [1.0, 1.0, 1.0],
            "night_txn_ratio": [0.0, 0.0, 0.0],
            "new_payee_ratio": [1.0, 0.0, 0.5],
            "account_age_days": [12.0, 500.0, 300.0],
            "txn_count_out": [1.0, 1.0, 2.0],
            "txn_count_in": [15.0, 1.0, 2.0],
            "total_out_inr": [28000.0, 500.0, 1200.0],
            "total_in_inr": [30000.0, 500.0, 1200.0],
            "avg_amount_out": [28000.0, 500.0, 600.0],
        },
        index=accounts,
    )

    contribs_df = pd.DataFrame(0.0, index=accounts, columns=FEATURE_COLUMNS)
    # ACC-00001
    contribs_df.loc["ACC-00001", "forward_ratio_15min"] = 1.456789
    contribs_df.loc["ACC-00001", "n_unique_senders"] = 2.123456
    contribs_df.loc["ACC-00001", "median_hold_minutes"] = 0.876543
    contribs_df.loc["ACC-00001", "account_age_days"] = 0.123456
    contribs_df.loc["ACC-00001", "night_txn_ratio"] = -0.5

    # ACC-00002 has all <= 0
    contribs_df.loc["ACC-00002", "n_unique_senders"] = -0.2
    contribs_df.loc["ACC-00002", "account_age_days"] = -0.8

    # ACC-00003
    contribs_df.loc["ACC-00003", "median_hold_minutes"] = 0.4321

    reasons = build_reasons(features_df, contribs_df, top_k=3)

    # 1. ACC-00001 should have top 3 positive, sorted desc: n_unique_senders (2.1235), forward_ratio_15min (1.4568), median_hold_minutes (0.8765)
    r1 = reasons["ACC-00001"]
    assert len(r1) == 3
    assert r1[0]["feature"] == "n_unique_senders"
    assert r1[0]["shap"] == 2.1235
    assert r1[0]["value"] == 15.0
    assert r1[0]["text"] == "Received money from 15 different senders"

    assert r1[1]["feature"] == "forward_ratio_15min"
    assert r1[1]["shap"] == 1.4568
    assert r1[1]["value"] == 0.92
    assert r1[1]["text"] == "Forwarded 92% of received money within 15 minutes"

    assert r1[2]["feature"] == "median_hold_minutes"
    assert r1[2]["shap"] == 0.8765
    assert r1[2]["value"] == 6.5
    assert r1[2]["text"] == "Typically moves money out 6 minutes after receiving it"

    # 2. ACC-00002 should have empty list
    assert reasons["ACC-00002"] == []

    # 3. ACC-00003 should have 1 item
    r3 = reasons["ACC-00003"]
    assert len(r3) == 1
    assert r3[0]["feature"] == "median_hold_minutes"
    assert r3[0]["shap"] == 0.4321
    assert r3[0]["value"] == 720.0
