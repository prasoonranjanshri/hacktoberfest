"""Generate plain-English explanation reasons from SHAP values."""

from typing import Any
import pandas as pd

TEMPLATES: dict[str, str] = {
    "n_unique_senders": "Received money from {v:.0f} different senders",
    "n_unique_receivers": "Sent money to {v:.0f} different receivers",
    "forward_ratio_15min": "Forwarded {v*100:.0f}% of received money within 15 minutes",
    "median_hold_minutes": "Typically moves money out {v:.0f} minutes after receiving it",
    "neighbour_mean_forward_ratio": "Connected accounts also forward {v*100:.0f}% of money quickly",
    "max_out_txns_10min": "Made up to {v:.0f} payments within 10 minutes",
    "night_txn_ratio": "{v*100:.0f}% of payments sent between midnight and 5 AM",
    "new_payee_ratio": "{v*100:.0f}% of payments went to first-time payees",
    "account_age_days": "Account is only {v:.0f} days old",
    "txn_count_out": "Sent {v:.0f} payments",
    "txn_count_in": "Received {v:.0f} payments",
    "total_out_inr": "Sent a total of INR {v:,.0f}",
    "total_in_inr": "Received a total of INR {v:,.0f}",
    "avg_amount_out": "Average payment sent is INR {v:,.0f}",
}


def format_reason_text(feature: str, v: float) -> str:
    """Render reason template using the actual feature value."""
    if feature == "n_unique_senders":
        return f"Received money from {v:.0f} different senders"
    elif feature == "n_unique_receivers":
        return f"Sent money to {v:.0f} different receivers"
    elif feature == "forward_ratio_15min":
        return f"Forwarded {v*100:.0f}% of received money within 15 minutes"
    elif feature == "median_hold_minutes":
        return f"Typically moves money out {v:.0f} minutes after receiving it"
    elif feature == "neighbour_mean_forward_ratio":
        return f"Connected accounts also forward {v*100:.0f}% of money quickly"
    elif feature == "max_out_txns_10min":
        return f"Made up to {v:.0f} payments within 10 minutes"
    elif feature == "night_txn_ratio":
        return f"{v*100:.0f}% of payments sent between midnight and 5 AM"
    elif feature == "new_payee_ratio":
        return f"{v*100:.0f}% of payments went to first-time payees"
    elif feature == "account_age_days":
        return f"Account is only {v:.0f} days old"
    elif feature == "txn_count_out":
        return f"Sent {v:.0f} payments"
    elif feature == "txn_count_in":
        return f"Received {v:.0f} payments"
    elif feature == "total_out_inr":
        return f"Sent a total of INR {v:,.0f}"
    elif feature == "total_in_inr":
        return f"Received a total of INR {v:,.0f}"
    elif feature == "avg_amount_out":
        return f"Average payment sent is INR {v:,.0f}"
    return f"{feature}: {v}"


def build_reasons(
    features: pd.DataFrame, contribs: pd.DataFrame, top_k: int = 3
) -> dict[str, list[dict[str, Any]]]:
    """Build up to top_k human-readable reason dictionaries for each account.

    Uses only positive-SHAP features sorted by shap descending.
    Each item contains: {"feature", "text", "shap", "value"}.
    """
    reasons_by_account: dict[str, list[dict[str, Any]]] = {}

    for account_id in features.index:
        c_row = contribs.loc[account_id]
        f_row = features.loc[account_id]

        pos_items = []
        for feat in contribs.columns:
            shap_val = float(c_row[feat])
            if shap_val > 0.0:
                pos_items.append((shap_val, feat))

        # Sort descending by shap value
        pos_items.sort(key=lambda x: x[0], reverse=True)

        selected = pos_items[:top_k]
        acc_reasons = []
        for s_val, feat_name in selected:
            real_val = float(f_row[feat_name])
            rendered_text = format_reason_text(feat_name, real_val)
            acc_reasons.append(
                {
                    "feature": feat_name,
                    "text": rendered_text,
                    "shap": round(s_val, 4),
                    "value": round(real_val, 4),
                }
            )

        reasons_by_account[str(account_id)] = acc_reasons

    return reasons_by_account
