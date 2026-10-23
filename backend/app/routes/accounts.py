"""Account details and ego-network graph endpoints."""

from fastapi import APIRouter, Depends, Query
from backend.app.config import DEFAULT_MAX_NODES
from backend.app.schemas import AccountDetailResponse, GraphResponse
from backend.app.services import alert_service, graph_service
from backend.app.store import require_loaded_store

router = APIRouter()


@router.get("/accounts/{account_id}", response_model=AccountDetailResponse)
def get_account(
    account_id: str,
    _store=Depends(require_loaded_store),
) -> AccountDetailResponse:
    """Retrieve details, features, and explainability reasons for account."""
    return alert_service.get_account_detail(account_id=account_id)


@router.get("/accounts/{account_id}/graph", response_model=GraphResponse)
def get_graph(
    account_id: str,
    hops: int = Query(default=1, description="Hops for ego network"),
    max_nodes: int = Query(default=DEFAULT_MAX_NODES, description="Max node limit"),
    _store=Depends(require_loaded_store),
) -> GraphResponse:
    """Retrieve ego-network graph centered on the specified account."""
    return graph_service.get_account_graph(
        account_id=account_id, hops=hops, max_nodes=max_nodes
    )
