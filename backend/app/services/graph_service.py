"""Network graph construction and ego network service."""

from backend.app.schemas import GraphResponse


def get_account_graph(
    account_id: str, hops: int = 1, max_nodes: int = 40
) -> GraphResponse:
    """Build ego-network subgraph around center account up to given hops and node limit."""
    raise NotImplementedError("Implemented by Dev 2")
