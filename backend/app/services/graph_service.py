"""Network graph construction and ego network service."""

from collections import defaultdict
from backend.app.config import (
    DEFAULT_MAX_NODES,
    HOPS_ALLOWED,
    MAX_NODES_MAX,
    MAX_NODES_MIN,
)
from backend.app.errors import (
    ACCOUNT_NOT_FOUND,
    APIError,
    INVALID_HOPS,
    INVALID_MAX_NODES,
)
from backend.app.schemas import GraphEdge, GraphNode, GraphResponse
from backend.app.store import require_loaded_store


def get_account_graph(
    account_id: str, hops: int = 1, max_nodes: int = DEFAULT_MAX_NODES
) -> GraphResponse:
    """Build ego-network subgraph around center account up to given hops and node limit."""
    # 1. Parameter Validation
    if hops not in HOPS_ALLOWED:
        raise APIError(
            code=INVALID_HOPS,
            message="Hops must be 1 or 2",
            status_code=422,
            details={"hops": hops},
        )

    if max_nodes < MAX_NODES_MIN or max_nodes > MAX_NODES_MAX:
        raise APIError(
            code=INVALID_MAX_NODES,
            message=f"max_nodes must be between {MAX_NODES_MIN} and {MAX_NODES_MAX}",
            status_code=422,
            details={"max_nodes": max_nodes},
        )

    store = require_loaded_store()
    accounts_df = store.accounts_df
    txns_df = store.transactions_df
    assert accounts_df is not None and txns_df is not None

    if account_id not in set(accounts_df["account_id"]):
        raise APIError(
            code=ACCOUNT_NOT_FOUND,
            message=f"Account '{account_id}' not found",
            status_code=404,
            details={"account_id": account_id},
        )

    # 2. Find 1-hop counterparties of center
    center_txns = txns_df[
        (txns_df["sender_id"] == account_id) | (txns_df["receiver_id"] == account_id)
    ]

    counterparties_1_amt: dict[str, float] = defaultdict(float)
    for row in center_txns.itertuples():
        s = getattr(row, "sender_id")
        r = getattr(row, "receiver_id")
        amt = float(getattr(row, "amount_inr"))
        peer = r if s == account_id else s
        if peer != account_id:
            counterparties_1_amt[peer] += amt

    # Rank 1-hop counterparties by total amount desc, account_id asc
    hop1_candidates = sorted(
        counterparties_1_amt.keys(),
        key=lambda peer: (-counterparties_1_amt[peer], peer),
    )

    truncated = False
    max_hop1 = max_nodes - 1  # 1 slot reserved for center
    if len(hop1_candidates) > max_hop1:
        selected_hop1 = hop1_candidates[:max_hop1]
        truncated = True
    else:
        selected_hop1 = hop1_candidates

    included_nodes = [account_id] + selected_hop1
    included_set = set(included_nodes)

    # 3. If hops == 2 and room remains, add 2-hop counterparties
    if hops == 2:
        remaining_capacity = max_nodes - len(included_nodes)
        if remaining_capacity > 0:
            hop1_set = set(selected_hop1)
            # Find counterparties of hop1 accounts
            hop2_txns = txns_df[
                (txns_df["sender_id"].isin(hop1_set))
                | (txns_df["receiver_id"].isin(hop1_set))
            ]
            counterparties_2_amt: dict[str, float] = defaultdict(float)
            for row in hop2_txns.itertuples():
                s = getattr(row, "sender_id")
                r = getattr(row, "receiver_id")
                amt = float(getattr(row, "amount_inr"))
                if s in hop1_set and r not in included_set:
                    counterparties_2_amt[r] += amt
                elif r in hop1_set and s not in included_set:
                    counterparties_2_amt[s] += amt

            hop2_candidates = sorted(
                counterparties_2_amt.keys(),
                key=lambda peer: (-counterparties_2_amt[peer], peer),
            )

            if len(hop2_candidates) > remaining_capacity:
                selected_hop2 = hop2_candidates[:remaining_capacity]
                truncated = True
            else:
                selected_hop2 = hop2_candidates

            included_nodes.extend(selected_hop2)
            included_set.update(selected_hop2)
        elif len(selected_hop1) > 0:
            # If no capacity left for 2-hop, but hop 1 had neighbors, check if hop 2 exists
            # Any dropped 2-hop neighbors mean truncated = True
            truncated = True

    # 4. Construct Node models
    acc_lookup = accounts_df.set_index("account_id")
    nodes: list[GraphNode] = []
    for nid in included_nodes:
        if nid in acc_lookup.index:
            score = float(acc_lookup.loc[nid, "risk_score"])
            is_f = bool(int(acc_lookup.loc[nid, "is_fraud"]) == 1)
        else:
            score = 0.0
            is_f = False

        nodes.append(
            GraphNode(
                id=nid,
                risk_score=round(score, 4),
                ground_truth_fraud=is_f,
                is_center=(nid == account_id),
            )
        )

    # 5. Construct Edge models (only between included nodes)
    subgraph_txns = txns_df[
        (txns_df["sender_id"].isin(included_set))
        & (txns_df["receiver_id"].isin(included_set))
    ]

    edges_map: dict[tuple[str, str], dict] = {}
    for row in subgraph_txns.itertuples():
        s = getattr(row, "sender_id")
        r = getattr(row, "receiver_id")
        amt = float(getattr(row, "amount_inr"))
        ts = str(getattr(row, "timestamp"))

        pair = (s, r)
        if pair not in edges_map:
            edges_map[pair] = {
                "txn_count": 0,
                "total_amount_inr": 0.0,
                "first_ts": ts,
                "last_ts": ts,
            }
        e = edges_map[pair]
        e["txn_count"] += 1
        e["total_amount_inr"] += amt
        if ts < e["first_ts"]:
            e["first_ts"] = ts
        if ts > e["last_ts"]:
            e["last_ts"] = ts

    edges: list[GraphEdge] = []
    for (s, r), data in sorted(edges_map.items()):
        edges.append(
            GraphEdge(
                source=s,
                target=r,
                txn_count=data["txn_count"],
                total_amount_inr=round(data["total_amount_inr"], 2),
                first_ts=data["first_ts"],
                last_ts=data["last_ts"],
            )
        )

    return GraphResponse(
        center_id=account_id,
        hops=hops,
        truncated=truncated,
        nodes=nodes,
        edges=edges,
    )
