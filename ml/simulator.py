"""Synthetic UPI-style transaction and account simulator for fraud detection."""

import pandas as pd


def generate_dataset(
    n_accounts: int, days: int, seed: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate synthetic accounts and transactions.

    Returns:
        tuple of (accounts_truth, transactions)
    """
    raise NotImplementedError("Implemented by Dev 1")
