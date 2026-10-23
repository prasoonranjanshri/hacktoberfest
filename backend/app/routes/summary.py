"""Summary endpoint."""

from fastapi import APIRouter, Depends
from backend.app.schemas import SummaryResponse
from backend.app.services import alert_service
from backend.app.store import require_loaded_store

router = APIRouter()


@router.get("/summary", response_model=SummaryResponse)
def get_summary(_store=Depends(require_loaded_store)) -> SummaryResponse:
    """Retrieve high-level dataset metrics and model cross-validation results."""
    return alert_service.get_summary()
