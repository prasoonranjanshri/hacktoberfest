"""Metrics computation utilities for MuleNet."""

from typing import Any, Optional, Sequence, Union
import numpy as np
import pandas as pd


def budget_metrics(
    y_true: Union[pd.Series, Sequence[Union[int, bool]]],
    scores: Union[pd.Series, Sequence[float]],
    budget: int,
    account_ids: Optional[Sequence[Any]] = None,
) -> dict[str, Union[int, float]]:
    """Compute fraud detection metrics for a fixed alert budget.

    Sorts by score descending, breaking ties by account_id / index ascending.
    Accepts pandas Series indexed by account_id or equal-length sequences.

    Returns:
        dict with alerts_returned, true_frauds_caught, false_alerts, recall, precision.
    """
    if isinstance(scores, pd.Series):
        scores_arr = scores.values
        if account_ids is None:
            account_ids = list(scores.index)
    else:
        scores_arr = np.asarray(scores)

    if isinstance(y_true, pd.Series):
        y_true_arr = (y_true.values == 1).astype(int)
    else:
        y_true_arr = (np.asarray(y_true) == 1).astype(int)

    n = len(scores_arr)
    if len(y_true_arr) != n:
        raise ValueError(f"Length mismatch: len(y_true)={len(y_true_arr)} != len(scores)={n}")

    if account_ids is None:
        ids_list = list(range(n))
    else:
        ids_list = list(account_ids)
        if len(ids_list) != n:
            raise ValueError(f"Length mismatch: len(account_ids)={len(ids_list)} != len(scores)={n}")

    # Build sorting list: item = (score, account_id, original_idx)
    # To sort score descending and account_id ascending:
    items = []
    for idx in range(n):
        items.append((scores_arr[idx], ids_list[idx], idx))

    # In Python, sort key can return (-score, id)
    # To handle heterogeneous ID types safely, we convert id to string if needed or use tuple
    items.sort(key=lambda x: (-float(x[0]), str(x[1]) if not isinstance(x[1], (int, float)) else x[1]))

    alerts_returned = min(max(int(budget), 0), n)
    selected_indices = [item[2] for item in items[:alerts_returned]]

    total_frauds = int(np.sum(y_true_arr))
    true_frauds_caught = int(sum(y_true_arr[i] for i in selected_indices))
    false_alerts = alerts_returned - true_frauds_caught

    recall = round(true_frauds_caught / total_frauds, 4) if total_frauds > 0 else 0.0
    precision = round(true_frauds_caught / alerts_returned, 4) if alerts_returned > 0 else 0.0

    return {
        "alerts_returned": alerts_returned,
        "true_frauds_caught": true_frauds_caught,
        "false_alerts": false_alerts,
        "recall": float(recall),
        "precision": float(precision),
    }
