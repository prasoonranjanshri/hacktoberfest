"""Generate plain-English explanation reasons from SHAP values."""

from typing import Any
import pandas as pd


def build_reasons(
    features: pd.DataFrame, contribs: pd.DataFrame, top_k: int = 3
) -> dict[str, list[dict[str, Any]]]:
    """Build up to top_k human-readable reason dictionaries for each account.

    Uses only positive-SHAP features sorted by shap descending.
    """
    raise NotImplementedError("Implemented by Dev 2")
