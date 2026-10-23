"""Alert and account analytics service."""

from backend.app.schemas import (
    AccountDetailResponse,
    AlertsResponse,
    BudgetCurveResponse,
    DriftResponse,
    SummaryResponse,
)


def get_summary() -> SummaryResponse:
    """Retrieve dataset summary and model performance metrics."""
    raise NotImplementedError("Implemented by Dev 2")


def get_alerts(budget: int = 100) -> AlertsResponse:
    """Compute and rank alerts within given budget with summary metrics."""
    raise NotImplementedError("Implemented by Dev 2")


def get_account_detail(account_id: str) -> AccountDetailResponse:
    """Retrieve full details, features, and explainability reasons for account."""
    raise NotImplementedError("Implemented by Dev 2")


def get_budget_curve() -> BudgetCurveResponse:
    """Compute budget sensitivity curve for full model vs behaviour-only ablation."""
    raise NotImplementedError("Implemented by Dev 2")


def get_drift() -> DriftResponse:
    """Retrieve model/data drift metrics if available."""
    raise NotImplementedError("Implemented by Dev 2")
