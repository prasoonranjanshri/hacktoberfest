"""Artifact schema definitions and validation logic."""

from pathlib import Path
import json
import re
from typing import Union
import pandas as pd

# Design Decision: "Behaviour-only" features are restricted to properties computable from
# an account's own outgoing transactions and profile alone, WITHOUT any flow relationship
# between incoming and outgoing money. Inflows (txn_count_in, total_in_inr) are network/flow
# properties that, when combined with outflow totals, allow decision trees to reconstruct
# flow balance and forwarding ratios. Therefore, txn_count_in and total_in_inr belong to
# NETWORK_FEATURES, ensuring the behaviour-only ablation isolates pure user behavior from flow dynamics.

BEHAVIOUR_FEATURES = [
    "txn_count_out",
    "total_out_inr",
    "avg_amount_out",
    "night_txn_ratio",
    "new_payee_ratio",
    "max_out_txns_10min",
    "account_age_days",
]

NETWORK_FEATURES = [
    "txn_count_in",
    "total_in_inr",
    "n_unique_senders",
    "n_unique_receivers",
    "forward_ratio_15min",
    "median_hold_minutes",
    "neighbour_mean_forward_ratio",
]

FEATURE_COLUMNS = BEHAVIOUR_FEATURES + NETWORK_FEATURES

TYPOLOGIES = ["fan_in_fan_out", "pass_through_chain", "burst_velocity"]

ACCOUNT_COLUMNS = [
    "account_id",
    "risk_score",
    "baseline_score",
    "is_fraud",
    "typology",
    "ring_id",
] + FEATURE_COLUMNS

TRANSACTION_COLUMNS = [
    "txn_id",
    "timestamp",
    "sender_id",
    "receiver_id",
    "amount_inr",
    "typology",
]

DATA_SOURCES = ["synthetic_pipeline", "sample_fixture"]

ACCOUNT_ID_PATTERN = re.compile(r"^ACC-\d{5}$")


def validate_artifacts(path: Union[str, Path]) -> list[str]:
    """Validate artifacts in directory path against schema contract.

    Returns a list of human-readable error strings (empty if valid).
    Never raises an exception on bad data.
    """
    errors: list[str] = []
    base_dir = Path(path)

    if not base_dir.exists() or not base_dir.is_dir():
        return [f"Artifacts directory not found: {base_dir}"]

    accounts_file = base_dir / "accounts.csv"
    txns_file = base_dir / "transactions.csv"
    reasons_file = base_dir / "reasons.json"
    metrics_file = base_dir / "metrics.json"

    for required_file, name in [
        (accounts_file, "accounts.csv"),
        (txns_file, "transactions.csv"),
        (reasons_file, "reasons.json"),
        (metrics_file, "metrics.json"),
    ]:
        if not required_file.exists():
            errors.append(f"Required artifact file missing: {name}")

    df_accounts = None
    df_txns = None
    account_ids_set = set()
    n_fraud_actual = 0

    # 1. Validate accounts.csv
    if accounts_file.exists():
        try:
            df_accounts = pd.read_csv(
                accounts_file,
                dtype={"account_id": str, "typology": str, "ring_id": str},
                keep_default_na=False,
            )
            # Column check (exact order and names)
            actual_cols = list(df_accounts.columns)
            if actual_cols != ACCOUNT_COLUMNS:
                errors.append(
                    f"accounts.csv columns mismatch. Expected {ACCOUNT_COLUMNS}, got {actual_cols}"
                )

            # Check missing values
            # Empty strings allowed only in typology/ring_id
            for col in actual_cols:
                if col in ["typology", "ring_id"]:
                    continue
                # Check for empty string or NaN
                if df_accounts[col].isna().any():
                    errors.append(f"accounts.csv has NaN values in column '{col}'")
                elif (df_accounts[col].astype(str).str.strip() == "").any():
                    errors.append(f"accounts.csv has empty values in column '{col}'")

            # Check account_id regex and uniqueness
            if "account_id" in df_accounts.columns:
                account_ids = df_accounts["account_id"].astype(str)
                non_matching = [
                    aid for aid in account_ids if not ACCOUNT_ID_PATTERN.match(aid)
                ]
                if non_matching:
                    errors.append(
                        f"accounts.csv has invalid account_id format (expected ^ACC-\\d{{5}}$): {non_matching[:5]}"
                    )
                if account_ids.duplicated().any():
                    duplicates = account_ids[account_ids.duplicated()].tolist()
                    errors.append(f"accounts.csv has duplicate account_ids: {duplicates[:5]}")
                account_ids_set = set(account_ids)

            # Check risk_score and baseline_score in [0, 1]
            for score_col in ["risk_score", "baseline_score"]:
                if score_col in df_accounts.columns:
                    try:
                        scores = pd.to_numeric(df_accounts[score_col])
                        if (scores < 0.0).any() or (scores > 1.0).any():
                            errors.append(
                                f"accounts.csv '{score_col}' values must be in [0, 1]"
                            )
                    except Exception as e:
                        errors.append(
                            f"accounts.csv '{score_col}' contains non-numeric values: {e}"
                        )

            # Check is_fraud in {0, 1}
            if "is_fraud" in df_accounts.columns:
                try:
                    fraud_vals = pd.to_numeric(df_accounts["is_fraud"])
                    if not set(fraud_vals.unique()).issubset({0, 1}):
                        errors.append(
                            f"accounts.csv 'is_fraud' must contain only 0 and 1, got {set(fraud_vals.unique())}"
                        )
                    n_fraud_actual = int(fraud_vals.sum())
                except Exception as e:
                    errors.append(f"accounts.csv 'is_fraud' contains non-numeric values: {e}")

        except Exception as e:
            errors.append(f"Failed to read accounts.csv: {e}")

    # 2. Validate transactions.csv
    if txns_file.exists():
        try:
            df_txns = pd.read_csv(
                txns_file,
                dtype={"sender_id": str, "receiver_id": str, "txn_id": str, "typology": str},
                keep_default_na=False,
            )
            actual_cols = list(df_txns.columns)
            if actual_cols != TRANSACTION_COLUMNS:
                errors.append(
                    f"transactions.csv columns mismatch. Expected {TRANSACTION_COLUMNS}, got {actual_cols}"
                )

            if "sender_id" in df_txns.columns and account_ids_set:
                missing_senders = set(df_txns["sender_id"]) - account_ids_set
                if missing_senders:
                    errors.append(
                        f"transactions.csv contains sender_ids not in accounts.csv: {list(missing_senders)[:5]}"
                    )

            if "receiver_id" in df_txns.columns and account_ids_set:
                missing_receivers = set(df_txns["receiver_id"]) - account_ids_set
                if missing_receivers:
                    errors.append(
                        f"transactions.csv contains receiver_ids not in accounts.csv: {list(missing_receivers)[:5]}"
                    )

        except Exception as e:
            errors.append(f"Failed to read transactions.csv: {e}")

    # 3. Validate reasons.json
    if reasons_file.exists():
        try:
            with open(reasons_file, "r", encoding="utf-8") as f:
                reasons_data = json.load(f)

            if not isinstance(reasons_data, dict):
                errors.append("reasons.json must be a JSON object (mapping account_id to list of reasons)")
            else:
                for aid, reason_list in reasons_data.items():
                    if account_ids_set and aid not in account_ids_set:
                        errors.append(f"reasons.json key '{aid}' not found in accounts.csv")
                    if not isinstance(reason_list, list):
                        errors.append(f"reasons.json entry for '{aid}' must be a list")
                        continue
                    for r in reason_list:
                        if not isinstance(r, dict):
                            errors.append(f"reasons.json reason item for '{aid}' must be a dict")
                            continue
                        for req_key in ["feature", "text", "shap", "value"]:
                            if req_key not in r:
                                errors.append(f"reasons.json reason item for '{aid}' missing key '{req_key}'")
                        if "feature" in r and r["feature"] not in FEATURE_COLUMNS:
                            errors.append(
                                f"reasons.json reason item for '{aid}' has invalid feature '{r['feature']}'. Must be in FEATURE_COLUMNS"
                            )
                        if "text" in r and not isinstance(r["text"], str):
                            errors.append(f"reasons.json reason item for '{aid}' text must be a string")
                        if "shap" in r and not isinstance(r["shap"], (int, float)):
                            errors.append(f"reasons.json reason item for '{aid}' shap must be a number")
                        if "value" in r and not isinstance(r["value"], (int, float)):
                            errors.append(f"reasons.json reason item for '{aid}' value must be a number")
        except Exception as e:
            errors.append(f"Failed to read reasons.json: {e}")

    # 4. Validate metrics.json
    if metrics_file.exists():
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                metrics_data = json.load(f)

            if not isinstance(metrics_data, dict):
                errors.append("metrics.json must be a JSON object")
            else:
                required_metric_keys = [
                    "data_source",
                    "generated_at",
                    "seed",
                    "n_accounts",
                    "n_transactions",
                    "n_fraud_accounts",
                    "typology_counts",
                    "cv",
                    "model",
                ]
                for key in required_metric_keys:
                    if key not in metrics_data:
                        errors.append(f"metrics.json missing key '{key}'")

                if "data_source" in metrics_data and metrics_data["data_source"] not in DATA_SOURCES:
                    errors.append(
                        f"metrics.json data_source '{metrics_data['data_source']}' not in {DATA_SOURCES}"
                    )

                if df_accounts is not None:
                    if "n_accounts" in metrics_data and metrics_data["n_accounts"] != len(df_accounts):
                        errors.append(
                            f"metrics.json n_accounts ({metrics_data['n_accounts']}) != accounts.csv count ({len(df_accounts)})"
                        )
                    if "n_fraud_accounts" in metrics_data and metrics_data["n_fraud_accounts"] != n_fraud_actual:
                        errors.append(
                            f"metrics.json n_fraud_accounts ({metrics_data['n_fraud_accounts']}) != accounts.csv fraud count ({n_fraud_actual})"
                        )

                if df_txns is not None:
                    if "n_transactions" in metrics_data and metrics_data["n_transactions"] != len(df_txns):
                        errors.append(
                            f"metrics.json n_transactions ({metrics_data['n_transactions']}) != transactions.csv count ({len(df_txns)})"
                        )

                if "cv" in metrics_data:
                    cv = metrics_data["cv"]
                    if not isinstance(cv, dict):
                        errors.append("metrics.json 'cv' must be an object")
                    else:
                        for cv_k in ["scheme", "n_splits"]:
                            if cv_k not in cv:
                                errors.append(f"metrics.json cv missing '{cv_k}'")

                if "model" in metrics_data:
                    model = metrics_data["model"]
                    if not isinstance(model, dict):
                        errors.append("metrics.json 'model' must be an object")
                    else:
                        for m_k in ["name", "pr_auc", "pr_auc_behaviour_only"]:
                            if m_k not in model:
                                errors.append(f"metrics.json model missing '{m_k}'")

        except Exception as e:
            errors.append(f"Failed to read metrics.json: {e}")

    return errors
