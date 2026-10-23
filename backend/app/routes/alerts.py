"""Alerts endpoint."""

from fastapi import APIRouter, Depends, Query
from backend.app.config import DEFAULT_BUDGET
from backend.app.schemas import AlertsResponse
from backend.app.services import alert_service
from backend.app.store import require_loaded_store

router = APIRouter()


@router.get("/alerts", response_model=AlertsResponse)
def get_alerts(
    budget: int = Query(default=DEFAULT_BUDGET, description="Alert budget"),
    _store=Depends(require_loaded_store),
) -> AlertsResponse:
    """Retrieve ranked alerts sized by budget with performance metrics."""
    return alert_service.get_alerts(budget=budget)
