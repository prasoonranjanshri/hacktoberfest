"""Pydantic v2 response and request schemas matching MuleNet API contract."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail


# GET /api/health
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    artifacts_loaded: bool
    data_source: Optional[str] = None
    generated_at: Optional[str] = None


# GET /api/summary
class DatasetSummary(BaseModel):
    n_accounts: int
    n_transactions: int
    n_fraud_accounts: int
    fraud_rate: float
    typology_counts: dict[str, int]


class ModelSummary(BaseModel):
    name: str
    cv_scheme: str
    cv_splits: int
    pr_auc: float
    pr_auc_behaviour_only: float


class SummaryResponse(BaseModel):
    data_source: str
    generated_at: str
    seed: int
    dataset: DatasetSummary
    model: ModelSummary


# GET /api/alerts
class BudgetSummary(BaseModel):
    alerts_returned: int
    true_frauds_caught: int
    false_alerts: int
    total_frauds: int
    recall: float
    precision: float
    false_alerts_per_1000_accounts: float
    behaviour_only_true_frauds_caught: int


class AlertItem(BaseModel):
    rank: int
    account_id: str
    risk_score: float
    top_reason: str
    ground_truth_fraud: bool
    true_typology: Optional[str] = None


class AlertsResponse(BaseModel):
    budget: int
    budget_summary: BudgetSummary
    alerts: list[AlertItem]


# GET /api/accounts/{account_id}
class ReasonItem(BaseModel):
    feature: str
    text: str
    shap: float
    value: float


class AccountDetailResponse(BaseModel):
    account_id: str
    rank: int
    risk_score: float
    baseline_score: float
    ground_truth_fraud: bool
    true_typology: Optional[str] = None
    ring_id: Optional[str] = None
    reasons: list[ReasonItem]
    features: dict[str, float]


# GET /api/accounts/{account_id}/graph
class GraphNode(BaseModel):
    id: str
    risk_score: float
    ground_truth_fraud: bool
    is_center: bool


class GraphEdge(BaseModel):
    source: str
    target: str
    txn_count: int
    total_amount_inr: float
    first_ts: str
    last_ts: str


class GraphResponse(BaseModel):
    center_id: str
    hops: int
    truncated: bool
    nodes: list[GraphNode]
    edges: list[GraphEdge]


# GET /api/budget-curve
class CurveSeries(BaseModel):
    true_frauds_caught: list[int]
    false_alerts: list[int]
    recall: list[float]


class BudgetCurveResponse(BaseModel):
    budgets: list[int]
    total_frauds: int
    total_accounts: int
    full: CurveSeries
    behaviour_only: CurveSeries


# GET /api/drift
class DriftWindow(BaseModel):
    window: str
    start: str
    end: str
    psi: float
    recall_frozen: float
    recall_retrained: float


class DriftResponse(BaseModel):
    available: bool
    windows: Optional[list[DriftWindow]] = None
    psi_alert_threshold: Optional[float] = None
    new_typology_window: Optional[str] = None
    note: Optional[str] = None
