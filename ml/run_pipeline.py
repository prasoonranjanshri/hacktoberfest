"""Orchestrate end-to-end ML pipeline and write output artifacts."""

import argparse
from datetime import datetime
import json
from pathlib import Path
import pandas as pd

from common.artifact_schema import (
    ACCOUNT_COLUMNS,
    BEHAVIOUR_FEATURES,
    FEATURE_COLUMNS,
    TRANSACTION_COLUMNS,
    validate_artifacts,
)
from common.metrics import budget_metrics
from ml.explain import build_reasons
from ml.features import build_features
from ml.simulator import generate_dataset
from ml.train_eval import cross_val_scores, pr_auc


def run(
    out_dir: str = "artifacts",
    seed: int = 42,
    n_accounts: int = 3000,
    days: int = 30,
) -> None:
    """Run full pipeline: simulate, extract features, train models, explain, validate, and write artifacts."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"=== MuleNet ML Pipeline: {n_accounts} accounts, {days} days, seed={seed} ===")

    # 1. Generate Dataset
    print("[1/5] Simulating synthetic transactions and accounts...")
    accounts_truth, transactions = generate_dataset(
        n_accounts=n_accounts, days=days, seed=seed
    )

    # 2. Extract Features
    print("[2/5] Extracting behavioural and network features...")
    features = build_features(transactions, accounts_truth)

    # 3. Train and Cross-Validate Models
    print("[3/5] Cross-validating XGBoost with GroupKFold...")
    groups = accounts_truth.apply(
        lambda row: row["ring_id"] if row["ring_id"] != "" else row["account_id"],
        axis=1,
    )
    groups.index = accounts_truth["account_id"]
    labels = accounts_truth.set_index("account_id")["is_fraud"]

    # Full Model (all 14 features)
    full_scores, full_contribs = cross_val_scores(
        features=features,
        labels=labels,
        groups=groups,
        feature_cols=FEATURE_COLUMNS,
        n_splits=5,
        seed=seed,
        return_contribs=True,
    )

    # Behaviour-only Model (9 features)
    beh_scores, _ = cross_val_scores(
        features=features,
        labels=labels,
        groups=groups,
        feature_cols=BEHAVIOUR_FEATURES,
        n_splits=5,
        seed=seed,
        return_contribs=False,
    )

    # Compute PR-AUC
    full_pr_auc = pr_auc(labels, full_scores)
    beh_pr_auc = pr_auc(labels, beh_scores)

    # Compute recall at budgets 50, 100, 150
    recalls_full = {}
    recalls_beh = {}
    for b in [50, 100, 150]:
        bm_full = budget_metrics(y_true=labels, scores=full_scores, budget=b)
        bm_beh = budget_metrics(y_true=labels, scores=beh_scores, budget=b)
        recalls_full[b] = bm_full["recall"]
        recalls_beh[b] = bm_beh["recall"]

    print("\n--- Pipeline Evaluation Metrics ---")
    print(f"Full Model PR-AUC:           {full_pr_auc:.4f}")
    print(f"Behaviour-only Model PR-AUC: {beh_pr_auc:.4f}")
    print(f"PR-AUC Improvement:          {(full_pr_auc - beh_pr_auc):+.4f}")
    for b in [50, 100, 150]:
        print(
            f"Recall @ Budget {b:3d}: Full = {recalls_full[b]:.4f} | Behaviour-only = {recalls_beh[b]:.4f} (diff: {recalls_full[b] - recalls_beh[b]:+.4f})"
        )
    print("-----------------------------------\n")

    # 4. Generate Explainability Reasons
    print("[4/5] Generating plain-English SHAP reasons...")
    assert full_contribs is not None
    reasons = build_reasons(features, full_contribs, top_k=3)

    # 5. Build and Write Artifacts
    print("[5/5] Writing artifacts...")
    # accounts.csv
    accounts_df = accounts_truth.copy()
    accounts_df["risk_score"] = [round(float(full_scores.loc[aid]), 4) for aid in accounts_df["account_id"]]
    accounts_df["baseline_score"] = [round(float(beh_scores.loc[aid]), 4) for aid in accounts_df["account_id"]]

    for col in FEATURE_COLUMNS:
        accounts_df[col] = [round(float(features.loc[aid, col]), 4) for aid in accounts_df["account_id"]]

    accounts_df = accounts_df[ACCOUNT_COLUMNS]
    accounts_df.to_csv(out_path / "accounts.csv", index=False)

    # transactions.csv
    txns_df = transactions.copy()
    txns_df["timestamp"] = pd.to_datetime(txns_df["timestamp"]).dt.strftime("%Y-%m-%dT%H:%M:%S")
    txns_df = txns_df[TRANSACTION_COLUMNS]
    txns_df.to_csv(out_path / "transactions.csv", index=False)

    # reasons.json
    with open(out_path / "reasons.json", "w", encoding="utf-8") as f:
        json.dump(reasons, f, indent=2)

    # metrics.json
    fraud_counts = accounts_truth[accounts_truth["is_fraud"] == 1]["typology"].value_counts().to_dict()
    metrics_data = {
        "data_source": "synthetic_pipeline",
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "seed": seed,
        "n_accounts": len(accounts_df),
        "n_transactions": len(txns_df),
        "n_fraud_accounts": int(accounts_df["is_fraud"].sum()),
        "typology_counts": {
            "fan_in_fan_out": int(fraud_counts.get("fan_in_fan_out", 0)),
            "pass_through_chain": int(fraud_counts.get("pass_through_chain", 0)),
            "burst_velocity": int(fraud_counts.get("burst_velocity", 0)),
        },
        "cv": {
            "scheme": "GroupKFold",
            "n_splits": 5,
        },
        "model": {
            "name": "xgboost",
            "pr_auc": round(float(full_pr_auc), 4),
            "pr_auc_behaviour_only": round(float(beh_pr_auc), 4),
        },
    }
    with open(out_path / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)

    # Validate output artifacts
    errors = validate_artifacts(out_path)
    if errors:
        raise RuntimeError(f"Artifact validation failed for '{out_path}':\n" + "\n".join(errors))

    print(f"Artifacts successfully written and validated in '{out_path}'.")


def main() -> None:
    """CLI entrypoint for running the ML pipeline."""
    parser = argparse.ArgumentParser(description="MuleNet ML pipeline runner")
    parser.add_argument("--out", default="artifacts", help="Output directory for artifacts")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--quick", action="store_true", help="Quick mode with 1000 accounts")
    parser.add_argument("--days", type=int, default=30, help="Simulation days")
    args = parser.parse_args()

    n_accounts = 1000 if args.quick else 3000
    run(out_dir=args.out, seed=args.seed, n_accounts=n_accounts, days=args.days)


if __name__ == "__main__":
    main()
