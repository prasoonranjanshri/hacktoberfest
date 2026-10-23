"""Model training and out-of-fold evaluation using XGBoost and GroupKFold."""

from typing import Any, Optional, Sequence
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
from sklearn.model_selection import GroupKFold
import xgboost as xgb


def pr_auc(y_true: Any, scores: Any) -> float:
    """Compute Precision-Recall Area Under Curve (PR-AUC) / Average Precision."""
    y_arr = np.asarray(y_true).astype(int)
    scores_arr = np.asarray(scores).astype(float)
    if np.sum(y_arr) == 0:
        return 0.0
    return float(average_precision_score(y_arr, scores_arr))


def cross_val_scores(
    features: pd.DataFrame,
    labels: pd.Series,
    groups: pd.Series,
    feature_cols: Sequence[str],
    n_splits: int = 5,
    seed: int = 42,
    return_contribs: bool = False,
) -> tuple[pd.Series, Optional[pd.DataFrame]]:
    """Train XGBoost model using GroupKFold cross-validation and return OOF scores.

    If return_contribs is True, returns OOF SHAP contributions from XGBoost pred_contribs
    with bias column dropped and columns set to feature_cols.
    """
    feature_cols_list = list(feature_cols)
    X = features[feature_cols_list].copy()
    y = pd.Series(labels.values, index=features.index).astype(int)
    g = pd.Series(groups.values, index=features.index)

    oof_scores = pd.Series(0.0, index=features.index, dtype=float, name="score")
    oof_contribs = (
        pd.DataFrame(0.0, index=features.index, columns=feature_cols_list, dtype=float)
        if return_contribs
        else None
    )

    gkf = GroupKFold(n_splits=n_splits)

    for train_idx, val_idx in gkf.split(X, y, groups=g):
        X_train = X.iloc[train_idx]
        y_train = y.iloc[train_idx]
        X_val = X.iloc[val_idx]

        n_pos = int(np.sum(y_train == 1))
        n_neg = int(len(y_train) - n_pos)
        scale_pos = (n_neg / n_pos) if n_pos > 0 else 1.0

        model = xgb.XGBClassifier(
            n_estimators=250,
            max_depth=4,
            learning_rate=0.05,
            tree_method="hist",
            scale_pos_weight=scale_pos,
            random_state=seed,
            eval_metric="logloss",
        )
        model.fit(X_train, y_train)

        # Predict probability of fraud (class 1)
        val_probs = model.predict_proba(X_val)[:, 1]
        oof_scores.iloc[val_idx] = val_probs

        if return_contribs and oof_contribs is not None:
            booster = model.get_booster()
            dval = xgb.DMatrix(X_val)
            # pred_contribs=True returns (N, num_features + 1), last column is bias
            contribs = booster.predict(dval, pred_contribs=True)
            # Drop the bias column
            contribs_no_bias = contribs[:, :-1]
            oof_contribs.iloc[val_idx] = contribs_no_bias

    return oof_scores, oof_contribs
