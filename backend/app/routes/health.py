"""Health endpoint."""

from fastapi import APIRouter
from backend.app.config import API_VERSION
from backend.app.schemas import HealthResponse
from backend.app.store import get_store

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Return API health and artifact status (works even when artifacts are not loaded)."""
    store = get_store()
    return HealthResponse(
        status="ok",
        service="mulenet-api",
        version=API_VERSION,
        artifacts_loaded=store.loaded,
        data_source=store.data_source,
        generated_at=store.generated_at,
    )
