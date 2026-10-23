"""Budget sensitivity curve endpoint."""

from fastapi import APIRouter, Depends
from backend.app.schemas import BudgetCurveResponse
from backend.app.services import alert_service
from backend.app.store import require_loaded_store

router = APIRouter()


@router.get("/budget-curve", response_model=BudgetCurveResponse)
def get_budget_curve(_store=Depends(require_loaded_store)) -> BudgetCurveResponse:
    """Retrieve full model vs behaviour-only budget sensitivity curves."""
    return alert_service.get_budget_curve()
