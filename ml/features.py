"""Feature extraction logic for behavioural and network features."""

from collections import defaultdict
import numpy as np
import pandas as pd

from common.artifact_schema import FEATURE_COLUMNS


def build_features(
    transactions: pd.DataFrame, accounts_truth: pd.DataFrame
) -> pd.DataFrame:
    """Build behavioural and network features from transactions and accounts.

    Returns:
        DataFrame indexed by account_id with exactly FEATURE_COLUMNS.
    """
    account_ids = list(accounts_truth["account_id"])
    account_set = set(account_ids)

    # Convert timestamps to numpy datetime64
    if not transactions.empty:
        txns = transactions.copy()
        if not np.issubdtype(txns["timestamp"].dtype, np.datetime64):
            txns["timestamp"] = pd.to_datetime(txns["timestamp"])
        txns.sort_values(by="timestamp", inplace=True)
    else:
        txns = pd.DataFrame(columns=["timestamp", "sender_id", "receiver_id", "amount_inr"])

    # Group transactions by sender and receiver
    out_txns_by_acc: dict[str, list[tuple[np.datetime64, float, str]]] = defaultdict(list)
    in_txns_by_acc: dict[str, list[tuple[np.datetime64, float, str]]] = defaultdict(list)

    for row in txns.itertuples():
        s = getattr(row, "sender_id")
        r = getattr(row, "receiver_id")
        amt = float(getattr(row, "amount_inr"))
        ts = np.datetime64(getattr(row, "timestamp"))

        if s in account_set:
            out_txns_by_acc[s].append((ts, amt, r))
        if r in account_set:
            in_txns_by_acc[r].append((ts, amt, s))

    # Pre-fetch account age mapping
    age_map = dict(zip(accounts_truth["account_id"], accounts_truth["account_age_days"]))

    ten_minutes = np.timedelta64(10, "m")
    fifteen_minutes = np.timedelta64(15, "m")

    # Dictionaries to collect computed features
    f_txn_count_out: dict[str, float] = {}
    f_txn_count_in: dict[str, float] = {}
    f_total_out_inr: dict[str, float] = {}
    f_total_in_inr: dict[str, float] = {}
    f_avg_amount_out: dict[str, float] = {}
    f_night_txn_ratio: dict[str, float] = {}
    f_new_payee_ratio: dict[str, float] = {}
    f_max_out_txns_10min: dict[str, float] = {}
    f_account_age_days: dict[str, float] = {}
    f_n_unique_senders: dict[str, float] = {}
    f_n_unique_receivers: dict[str, float] = {}
    f_forward_ratio_15min: dict[str, float] = {}
    f_median_hold_minutes: dict[str, float] = {}

    counterparties_by_acc: dict[str, set[str]] = defaultdict(set)

    for aid in account_ids:
        out_list = out_txns_by_acc.get(aid, [])
        in_list = in_txns_by_acc.get(aid, [])

        # Age
        f_account_age_days[aid] = float(age_map.get(aid, 0.0))

        # Basic counts & amounts
        n_out = len(out_list)
        n_in = len(in_list)
        f_txn_count_out[aid] = float(n_out)
        f_txn_count_in[aid] = float(n_in)

        out_amts = [item[1] for item in out_list]
        in_amts = [item[1] for item in in_list]

        tot_out = float(sum(out_amts))
        tot_in = float(sum(in_amts))
        f_total_out_inr[aid] = tot_out
        f_total_in_inr[aid] = tot_in

        # avg_amount_out
        f_avg_amount_out[aid] = (tot_out / n_out) if n_out > 0 else 0.0

        # Unique counterparties
        receivers = {item[2] for item in out_list if item[2] != aid}
        senders = {item[2] for item in in_list if item[2] != aid}
        f_n_unique_receivers[aid] = float(len(receivers))
        f_n_unique_senders[aid] = float(len(senders))

        counterparties_by_acc[aid] = receivers.union(senders)

        # new_payee_ratio
        f_new_payee_ratio[aid] = (float(len(receivers)) / n_out) if n_out > 0 else 0.0

        # Outgoing timestamps
        out_times = np.array([item[0] for item in out_list], dtype="datetime64[ns]")
        in_times = np.array([item[0] for item in in_list], dtype="datetime64[ns]")

        # night_txn_ratio (00:00 to 05:00)
        if n_out > 0:
            # hour in [0, 4]
            # Convert to pandas series for hour extraction
            hours = pd.DatetimeIndex(out_times).hour
            night_count = int(np.sum((hours >= 0) & (hours < 5)))
            f_night_txn_ratio[aid] = night_count / n_out
        else:
            f_night_txn_ratio[aid] = 0.0

        # max_out_txns_10min
        if n_out > 0:
            window_ends = out_times + ten_minutes
            j = np.searchsorted(out_times, window_ends, side="right")
            counts = j - np.arange(n_out)
            f_max_out_txns_10min[aid] = float(np.max(counts))
        else:
            f_max_out_txns_10min[aid] = 0.0

        # forward_ratio_15min:
        # sum of outgoing amounts within 15 min after any incoming payment, capped at total_in_inr / total_in_inr
        if n_in > 0 and n_out > 0 and tot_in > 0.0:
            forwarded_out_sum = 0.0
            for o_ts, o_amt, _ in out_list:
                # Find most recent incoming before or at o_ts
                idx = np.searchsorted(in_times, o_ts, side="right") - 1
                if idx >= 0:
                    diff = o_ts - in_times[idx]
                    if diff >= np.timedelta64(0, "ns") and diff <= fifteen_minutes:
                        forwarded_out_sum += o_amt
            forwarded_capped = min(forwarded_out_sum, tot_in)
            f_forward_ratio_15min[aid] = float(np.clip(forwarded_capped / tot_in, 0.0, 1.0))
        else:
            f_forward_ratio_15min[aid] = 0.0

        # median_hold_minutes:
        # median over incoming txns of the minutes until the account's next outgoing txn, capped at 1440, and 1440 if none or no incoming
        if n_in > 0:
            hold_times = []
            for i_ts in in_times:
                if n_out > 0:
                    idx = np.searchsorted(out_times, i_ts, side="left")
                    if idx < n_out:
                        diff_sec = (out_times[idx] - i_ts) / np.timedelta64(1, "s")
                        diff_min = max(0.0, diff_sec / 60.0)
                        hold_times.append(min(diff_min, 1440.0))
                    else:
                        hold_times.append(1440.0)
                else:
                    hold_times.append(1440.0)
            f_median_hold_minutes[aid] = float(np.median(hold_times))
        else:
            f_median_hold_minutes[aid] = 1440.0

    # neighbour_mean_forward_ratio:
    # mean forward_ratio_15min over distinct counterparties (senders and receivers), 0 if none
    f_neighbour_mean_forward_ratio: dict[str, float] = {}
    for aid in account_ids:
        c_parties = counterparties_by_acc[aid]
        if c_parties:
            nbr_ratios = [f_forward_ratio_15min.get(nbr, 0.0) for nbr in c_parties if nbr in account_set]
            if nbr_ratios:
                f_neighbour_mean_forward_ratio[aid] = float(np.mean(nbr_ratios))
            else:
                f_neighbour_mean_forward_ratio[aid] = 0.0
        else:
            f_neighbour_mean_forward_ratio[aid] = 0.0

    # Assemble final DataFrame
    features_data = {
        "txn_count_out": [f_txn_count_out[aid] for aid in account_ids],
        "txn_count_in": [f_txn_count_in[aid] for aid in account_ids],
        "total_out_inr": [f_total_out_inr[aid] for aid in account_ids],
        "total_in_inr": [f_total_in_inr[aid] for aid in account_ids],
        "avg_amount_out": [f_avg_amount_out[aid] for aid in account_ids],
        "night_txn_ratio": [f_night_txn_ratio[aid] for aid in account_ids],
        "new_payee_ratio": [f_new_payee_ratio[aid] for aid in account_ids],
        "max_out_txns_10min": [f_max_out_txns_10min[aid] for aid in account_ids],
        "account_age_days": [f_account_age_days[aid] for aid in account_ids],
        "n_unique_senders": [f_n_unique_senders[aid] for aid in account_ids],
        "n_unique_receivers": [f_n_unique_receivers[aid] for aid in account_ids],
        "forward_ratio_15min": [f_forward_ratio_15min[aid] for aid in account_ids],
        "median_hold_minutes": [f_median_hold_minutes[aid] for aid in account_ids],
        "neighbour_mean_forward_ratio": [
            f_neighbour_mean_forward_ratio[aid] for aid in account_ids
        ],
    }

    df_features = pd.DataFrame(features_data, index=account_ids)
    # Ensure exact column ordering
    df_features = df_features[FEATURE_COLUMNS]
    return df_features
