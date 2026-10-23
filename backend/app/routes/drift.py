"""Data and model drift endpoint."""

from fastapi import APIRouter, Depends
from backend.app.schemas import DriftResponse
from backend.app.services import alert_service
from backend.app.store import require_loaded_store

router = APIRouter()


@router.get("/drift", response_model=DriftResponse)
def get_drift(_store=Depends(require_loaded_store)) -> DriftResponse:
    """Retrieve precomputed drift metrics if available."""
    return alert_service.get_drift()
