"""Tests for common/metrics.py."""

import pandas as pd
from common.metrics import budget_metrics


def test_budget_metrics_hand_computed():
    """Verify budget_metrics against a hand-computed scenario."""
    # 5 accounts: 2 frauds, 3 legitimate
    y_true = [1, 0, 1, 0, 0]
    scores = [0.9, 0.8, 0.7, 0.4, 0.1]
    account_ids = ["ACC-00001", "ACC-00002", "ACC-00003", "ACC-00004", "ACC-00005"]

    # Budget = 2: picks ACC-00001 (fraud=1) and ACC-00002 (fraud=0)
    res = budget_metrics(y_true, scores, budget=2, account_ids=account_ids)
    assert res["alerts_returned"] == 2
    assert res["true_frauds_caught"] == 1
    assert res["false_alerts"] == 1
    assert res["recall"] == 0.5
    assert res["precision"] == 0.5

    # Budget = 3: picks ACC-00001, ACC-00002, ACC-00003 (both frauds caught)
    res3 = budget_metrics(y_true, scores, budget=3, account_ids=account_ids)
    assert res3["alerts_returned"] == 3
    assert res3["true_frauds_caught"] == 2
    assert res3["false_alerts"] == 1
    assert res3["recall"] == 1.0
    assert res3["precision"] == round(2 / 3, 4)


def test_budget_metrics_tie_break():
    """Verify tie breaking by account_id ascending when scores are equal."""
    # Two accounts with identical score 0.80.
    # ACC-00001 is fraud (1), ACC-00002 is legitimate (0).
    # Even if ACC-00002 appears first in the input, tie-break must prioritize ACC-00001.
    scores = pd.Series([0.80, 0.80], index=["ACC-00002", "ACC-00001"])
    y_true = pd.Series([0, 1], index=["ACC-00002", "ACC-00001"])

    res = budget_metrics(y_true, scores, budget=1)
    assert res["alerts_returned"] == 1
    # ACC-00001 should be chosen because "ACC-00001" < "ACC-00002"
    assert res["true_frauds_caught"] == 1
    assert res["false_alerts"] == 0
    assert res["precision"] == 1.0
    assert res["recall"] == 1.0


def test_budget_metrics_zero_frauds_and_budget_exceeds():
    """Verify edge cases: no frauds in ground truth, and budget larger than dataset."""
    y_true = [0, 0, 0]
    scores = [0.5, 0.3, 0.1]
    res = budget_metrics(y_true, scores, budget=10)
    assert res["alerts_returned"] == 3
    assert res["true_frauds_caught"] == 0
    assert res["false_alerts"] == 3
    assert res["recall"] == 0.0
    assert res["precision"] == 0.0
