"""Feature extraction logic for behavioural and network features."""

import pandas as pd


def build_features(
    transactions: pd.DataFrame, accounts_truth: pd.DataFrame
) -> pd.DataFrame:
    """Build behavioural and network features from transactions and accounts.

    Returns:
        DataFrame indexed by account_id with exactly FEATURE_COLUMNS.
    """
    raise NotImplementedError("Implemented by Dev 1")
