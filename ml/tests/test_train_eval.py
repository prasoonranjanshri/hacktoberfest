"""Tests for ml.train_eval."""

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import GroupKFold

from common.artifact_schema import BEHAVIOUR_FEATURES, FEATURE_COLUMNS
from ml.features import build_features
from ml.simulator import generate_dataset
from ml.train_eval import cross_val_scores, pr_auc


def test_cross_val_and_ring_isolation():
    """Verify GroupKFold isolation, score ranges, contribs columns, and PR-AUC comparison on quick data."""
    accounts_truth, txns = generate_dataset(n_accounts=1000, days=30, seed=42)
    features = build_features(txns, accounts_truth)

    # Prepare groups: non-empty ring_id, otherwise account_id
    groups = accounts_truth.apply(
        lambda row: row["ring_id"] if row["ring_id"] != "" else row["account_id"],
        axis=1,
    )
    groups.index = accounts_truth["account_id"]
    labels = accounts_truth.set_index("account_id")["is_fraud"]

    # 1. Verify no ring spans train and test
    gkf = GroupKFold(n_splits=5)
    rings_only = accounts_truth[accounts_truth["ring_id"] != ""]
    ring_ids_set = set(rings_only["ring_id"].unique())

    for train_idx, val_idx in gkf.split(features, labels, groups=groups):
        train_groups = set(groups.iloc[train_idx])
        val_groups = set(groups.iloc[val_idx])
        # Intersection between train and test groups must be empty
        overlap = train_groups.intersection(val_groups)
        assert len(overlap) == 0

        # Specifically for rings:
        overlap_rings = (train_groups.intersection(ring_ids_set)).intersection(
            val_groups.intersection(ring_ids_set)
        )
        assert len(overlap_rings) == 0

    # 2. Run full model with contribs
    full_scores, contribs = cross_val_scores(
        features=features,
        labels=labels,
        groups=groups,
        feature_cols=FEATURE_COLUMNS,
        n_splits=5,
        seed=42,
        return_contribs=True,
    )

    assert len(full_scores) == 1000
    assert (full_scores >= 0.0).all() and (full_scores <= 1.0).all()
    assert contribs is not None
    assert list(contribs.columns) == FEATURE_COLUMNS
    assert len(contribs) == 1000
    assert not contribs.isna().any().any()

    # 3. Run behaviour-only model
    beh_scores, _ = cross_val_scores(
        features=features,
        labels=labels,
        groups=groups,
        feature_cols=BEHAVIOUR_FEATURES,
        n_splits=5,
        seed=42,
        return_contribs=False,
    )

    full_prauc = pr_auc(labels, full_scores)
    beh_prauc = pr_auc(labels, beh_scores)

    assert full_prauc > 0.0
    assert beh_prauc > 0.0
    # Full model with graph features should match or outperform behaviour-only
    assert full_prauc >= beh_prauc


def test_pr_auc_edge_cases():
    """Verify pr_auc edge case behaviour."""
    assert pr_auc([0, 0, 0], [0.1, 0.2, 0.3]) == 0.0
    perfect = pr_auc([0, 1, 0, 1], [0.1, 0.9, 0.2, 0.8])
    assert perfect == 1.0
