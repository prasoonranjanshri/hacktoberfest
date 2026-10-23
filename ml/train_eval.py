"""Model training and out-of-fold evaluation."""

from typing import Optional, Sequence
import pandas as pd


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
    raise NotImplementedError("Implemented by Dev 1")
