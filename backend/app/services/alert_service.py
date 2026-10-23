"""Alert and account analytics service."""

from backend.app.config import (
    BUDGET_MAX,
    BUDGET_MIN,
    CURVE_BUDGETS,
    DEFAULT_BUDGET,
)
from backend.app.errors import (
    ACCOUNT_NOT_FOUND,
    APIError,
    INVALID_BUDGET,
)
from backend.app.schemas import (
    AccountDetailResponse,
    AlertItem,
    AlertsResponse,
    BudgetCurveResponse,
    BudgetSummary,
    CurveSeries,
    DatasetSummary,
    DriftResponse,
    ModelSummary,
    ReasonItem,
    SummaryResponse,
)
from backend.app.store import require_loaded_store
from common.artifact_schema import FEATURE_COLUMNS
from common.metrics import budget_metrics


def get_summary() -> SummaryResponse:
    """Retrieve dataset summary and model performance metrics."""
    store = require_loaded_store()
    metrics = store.metrics or {}
    dataset_info = {
        "n_accounts": metrics.get("n_accounts", len(store.accounts_df)),
        "n_transactions": metrics.get("n_transactions", len(store.transactions_df)),
        "n_fraud_accounts": metrics.get(
            "n_fraud_accounts", int(store.accounts_df["is_fraud"].sum())
        ),
        "fraud_rate": round(
            float(
                metrics.get(
                    "n_fraud_accounts", int(store.accounts_df["is_fraud"].sum())
                )
                / metrics.get("n_accounts", len(store.accounts_df))
            ),
            4,
        ),
        "typology_counts": metrics.get("typology_counts", {}),
    }

    model_raw = metrics.get("model", {})
    cv_raw = metrics.get("cv", {})
    model_info = {
        "name": model_raw.get("name", "xgboost"),
        "cv_scheme": cv_raw.get("scheme", "GroupKFold"),
        "cv_splits": cv_raw.get("n_splits", 5),
        "pr_auc": float(model_raw.get("pr_auc", 0.0)),
        "pr_auc_behaviour_only": float(model_raw.get("pr_auc_behaviour_only", 0.0)),
    }

    return SummaryResponse(
        data_source=store.data_source or "synthetic_pipeline",
        generated_at=store.generated_at or "",
        seed=metrics.get("seed", 42),
        dataset=DatasetSummary(**dataset_info),
        model=ModelSummary(**model_info),
    )


def get_alerts(budget: int = DEFAULT_BUDGET) -> AlertsResponse:
    """Compute and rank alerts within given budget with summary metrics."""
    if budget < BUDGET_MIN or budget > BUDGET_MAX:
        raise APIError(
            code=INVALID_BUDGET,
            message=f"Budget must be between {BUDGET_MIN} and {BUDGET_MAX}",
            status_code=422,
            details={"budget": budget},
        )

    store = require_loaded_store()
    df = store.accounts_df
    assert df is not None

    account_ids = list(df["account_id"])
    y_true = df["is_fraud"]
    risk_scores = df["risk_score"]
    baseline_scores = df["baseline_score"]

    bm_full = budget_metrics(
        y_true=y_true, scores=risk_scores, budget=budget, account_ids=account_ids
    )
    bm_beh = budget_metrics(
        y_true=y_true, scores=baseline_scores, budget=budget, account_ids=account_ids
    )

    n_accounts = len(df)
    false_alerts_per_1000 = (
        round(bm_full["false_alerts"] / n_accounts * 1000.0, 4)
        if n_accounts > 0
        else 0.0
    )

    budget_summary = BudgetSummary(
        alerts_returned=bm_full["alerts_returned"],
        true_frauds_caught=bm_full["true_frauds_caught"],
        false_alerts=bm_full["false_alerts"],
        total_frauds=int(y_true.sum()),
        recall=round(float(bm_full["recall"]), 4),
        precision=round(float(bm_full["precision"]), 4),
        false_alerts_per_1000_accounts=false_alerts_per_1000,
        behaviour_only_true_frauds_caught=bm_beh["true_frauds_caught"],
    )

    # Order alerts by (-risk_score, account_id)
    items = []
    reasons_map = store.reasons or {}
    for row in df.itertuples():
        aid = getattr(row, "account_id")
        score = float(getattr(row, "risk_score"))
        items.append((score, aid, row))

    items.sort(key=lambda x: (-x[0], x[1]))

    selected = items[:budget]
    alerts_list = []
    for rank_idx, (score, aid, row) in enumerate(selected):
        acc_reasons = reasons_map.get(aid, [])
        top_reason = (
            acc_reasons[0]["text"] if acc_reasons else "No strong risk indicators"
        )
        is_f = int(getattr(row, "is_fraud")) == 1
        typo = getattr(row, "typology")
        alerts_list.append(
            AlertItem(
                rank=rank_idx + 1,
                account_id=aid,
                risk_score=round(score, 4),
                top_reason=top_reason,
                ground_truth_fraud=is_f,
                true_typology=typo if typo else None,
            )
        )

    return AlertsResponse(
        budget=budget,
        budget_summary=budget_summary,
        alerts=alerts_list,
    )


def get_account_detail(account_id: str) -> AccountDetailResponse:
    """Retrieve full details, features, and explainability reasons for account."""
    store = require_loaded_store()
    df = store.accounts_df
    assert df is not None

    row_match = df[df["account_id"] == account_id]
    if row_match.empty:
        raise APIError(
            code=ACCOUNT_NOT_FOUND,
            message=f"Account '{account_id}' not found",
            status_code=404,
            details={"account_id": account_id},
        )

    row = row_match.iloc[0]

    # Calculate 1-based rank over all accounts
    # Ordering: risk_score desc, account_id asc
    items = []
    for r in df.itertuples():
        items.append((float(getattr(r, "risk_score")), getattr(r, "account_id")))
    items.sort(key=lambda x: (-x[0], x[1]))

    rank = 1
    for idx, (_, aid) in enumerate(items):
        if aid == account_id:
            rank = idx + 1
            break

    reasons_list_raw = (store.reasons or {}).get(account_id, [])
    reasons = [
        ReasonItem(
            feature=item["feature"],
            text=item["text"],
            shap=float(item["shap"]),
            value=float(item["value"]),
        )
        for item in reasons_list_raw
    ]

    features_dict = {}
    for col in FEATURE_COLUMNS:
        features_dict[col] = float(row[col])

    typo = row["typology"]
    ring = row["ring_id"]

    return AccountDetailResponse(
        account_id=account_id,
        rank=rank,
        risk_score=round(float(row["risk_score"]), 4),
        baseline_score=round(float(row["baseline_score"]), 4),
        ground_truth_fraud=bool(int(row["is_fraud"]) == 1),
        true_typology=typo if typo else None,
        ring_id=ring if ring else None,
        reasons=reasons,
        features=features_dict,
    )


def get_budget_curve() -> BudgetCurveResponse:
    """Compute budget sensitivity curve for full model vs behaviour-only ablation."""
    store = require_loaded_store()
    df = store.accounts_df
    assert df is not None

    account_ids = list(df["account_id"])
    y_true = df["is_fraud"]
    risk_scores = df["risk_score"]
    baseline_scores = df["baseline_score"]

    n_acc = len(df)
    budgets = [min(b, n_acc) for b in CURVE_BUDGETS]
    # Remove duplicates if capped
    budgets = sorted(list(dict.fromkeys(budgets)))

    full_caught = []
    full_false = []
    full_recall = []

    beh_caught = []
    beh_false = []
    beh_recall = []

    for b in budgets:
        m_full = budget_metrics(y_true, risk_scores, budget=b, account_ids=account_ids)
        full_caught.append(m_full["true_frauds_caught"])
        full_false.append(m_full["false_alerts"])
        full_recall.append(round(float(m_full["recall"]), 4))

        m_beh = budget_metrics(y_true, baseline_scores, budget=b, account_ids=account_ids)
        beh_caught.append(m_beh["true_frauds_caught"])
        beh_false.append(m_beh["false_alerts"])
        beh_recall.append(round(float(m_beh["recall"]), 4))

    return BudgetCurveResponse(
        budgets=budgets,
        total_frauds=int(y_true.sum()),
        total_accounts=n_acc,
        full=CurveSeries(
            true_frauds_caught=full_caught,
            false_alerts=full_false,
            recall=full_recall,
        ),
        behaviour_only=CurveSeries(
            true_frauds_caught=beh_caught,
            false_alerts=beh_false,
            recall=beh_recall,
        ),
    )


def get_drift() -> DriftResponse:
    """Retrieve model/data drift metrics if available."""
    store = require_loaded_store()
    if store.drift is None or not store.drift.get("available", False):
        return DriftResponse(available=False)
    return DriftResponse(**store.drift)
