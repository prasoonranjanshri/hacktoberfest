"""Synthetic UPI-style transaction and account simulator for fraud detection."""

from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
import pandas as pd

from ml.config import (
    BURST_VELOCITY_ACCOUNTS,
    BURST_VELOCITY_AMOUNT_MAX_INR,
    BURST_VELOCITY_AMOUNT_MIN_INR,
    BURST_VELOCITY_OUT_TXNS_MAX,
    BURST_VELOCITY_OUT_TXNS_MIN,
    BURST_VELOCITY_RECEIVERS_MAX,
    BURST_VELOCITY_RECEIVERS_MIN,
    DEFAULT_DAYS,
    DEFAULT_N_ACCOUNTS,
    DEFAULT_SEED,
    FAN_IN_ACCOUNTS,
    FAN_IN_AMOUNT_MAX_INR,
    FAN_IN_AMOUNT_MIN_INR,
    FAN_IN_FAN_OUT_RINGS,
    FAN_IN_MULES_PER_RING,
    FAN_IN_NEW_AGE_MAX_DAYS,
    FAN_IN_NEW_AGE_MIN_DAYS,
    FAN_IN_OLD_AGE_MAX_DAYS,
    FAN_IN_OLD_AGE_MIN_DAYS,
    FAN_IN_OLD_AGE_RATIO,
    NORMAL_AGE_MAX_DAYS,
    NORMAL_AGE_MIN_DAYS,
    NORMAL_AGGREGATOR_SHARE,
    NORMAL_MERCHANT_SHARE,
    NORMAL_NIGHT_ACTIVE_SHARE,
    NORMAL_PAYROLL_SHARE,
    PASS_THROUGH_CHAINS,
    PASS_THROUGH_FEE_RATIO,
    PASS_THROUGH_HOPS_PER_CHAIN,
    PASS_THROUGH_SENDERS_MAX,
    PASS_THROUGH_SENDERS_MIN,
)


def generate_dataset(
    n_accounts: int = DEFAULT_N_ACCOUNTS,
    days: int = DEFAULT_DAYS,
    seed: int = DEFAULT_SEED,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate realistic synthetic accounts and transactions.

    Returns:
        tuple of (accounts_truth, transactions)
    """
    rng = np.random.default_rng(seed)
    base_start_time = datetime(2026, 9, 1, 0, 0, 0)

    # 1. Scaling for quick mode
    scale = n_accounts / 3000.0
    if n_accounts == DEFAULT_N_ACCOUNTS:
        n_fan_in_rings = FAN_IN_FAN_OUT_RINGS
        n_chains = PASS_THROUGH_CHAINS
        n_burst = BURST_VELOCITY_ACCOUNTS
    else:
        n_fan_in_rings = max(1, int(round(FAN_IN_FAN_OUT_RINGS * scale)))
        n_chains = max(1, int(round(PASS_THROUGH_CHAINS * scale)))
        n_burst = max(1, int(round(BURST_VELOCITY_ACCOUNTS * scale)))

    n_fan_in = n_fan_in_rings * (FAN_IN_MULES_PER_RING + 1)
    n_chain_accounts = n_chains * PASS_THROUGH_HOPS_PER_CHAIN
    n_fraud = n_fan_in + n_chain_accounts + n_burst
    n_normal = n_accounts - n_fraud

    if n_normal <= 0:
        raise ValueError(f"Too few accounts ({n_accounts}) for {n_fraud} fraud accounts.")

    # 2. Account IDs - Shuffle to eliminate label leakage / contiguous ID block
    all_account_ids = [f"ACC-{i:05d}" for i in range(1, n_accounts + 1)]
    shuffled_ids = rng.permutation(all_account_ids).tolist()

    idx = 0
    fan_in_ids = shuffled_ids[idx : idx + n_fan_in]
    idx += n_fan_in
    chain_ids = shuffled_ids[idx : idx + n_chain_accounts]
    idx += n_chain_accounts
    burst_ids = shuffled_ids[idx : idx + n_burst]
    idx += n_burst
    normal_ids = shuffled_ids[idx : idx + n_normal]

    # Subdivide normal accounts
    n_merchants = max(1, int(round(n_normal * NORMAL_MERCHANT_SHARE)))
    n_payroll = max(1, int(round(n_normal * NORMAL_PAYROLL_SHARE)))
    n_aggregators = max(1, int(round(n_normal * NORMAL_AGGREGATOR_SHARE)))
    n_night_active = max(1, int(round(n_normal * NORMAL_NIGHT_ACTIVE_SHARE)))
    # ~4% family/peer expense poolers (hard negatives for fan-in and fast forwarding)
    n_poolers = max(1, int(round(n_normal * 0.04)))
    n_ordinary = n_normal - (n_merchants + n_payroll + n_aggregators + n_night_active + n_poolers)

    n_idx = 0
    ordinary_ids = normal_ids[n_idx : n_idx + n_ordinary]
    n_idx += n_ordinary
    merchant_ids = normal_ids[n_idx : n_idx + n_merchants]
    n_idx += n_merchants
    payroll_ids = normal_ids[n_idx : n_idx + n_payroll]
    n_idx += n_payroll
    aggregator_ids = normal_ids[n_idx : n_idx + n_aggregators]
    n_idx += n_aggregators
    night_active_ids = normal_ids[n_idx : n_idx + n_night_active]
    n_idx += n_night_active
    pooler_ids = normal_ids[n_idx:]

    account_rows = []

    # Fan-in rings
    fan_in_ring_groups = []
    for r in range(n_fan_in_rings):
        ring_id = f"RING-{r+1:03d}"
        collector_id = fan_in_ids[r * 5]
        mule_ids = fan_in_ids[r * 5 + 1 : (r + 1) * 5]
        fan_in_ring_groups.append((ring_id, collector_id, mule_ids))

        # Collector
        collector_age = float(rng.uniform(30.0, 800.0))
        account_rows.append(
            {
                "account_id": collector_id,
                "account_age_days": round(collector_age, 1),
                "is_fraud": 1,
                "typology": "fan_in_fan_out",
                "ring_id": ring_id,
            }
        )

        # Mules
        for m_id in mule_ids:
            if rng.random() < FAN_IN_OLD_AGE_RATIO:
                mule_age = float(rng.uniform(FAN_IN_OLD_AGE_MIN_DAYS, FAN_IN_OLD_AGE_MAX_DAYS))
            else:
                mule_age = float(rng.uniform(FAN_IN_NEW_AGE_MIN_DAYS, FAN_IN_NEW_AGE_MAX_DAYS))
            account_rows.append(
                {
                    "account_id": m_id,
                    "account_age_days": round(mule_age, 1),
                    "is_fraud": 1,
                    "typology": "fan_in_fan_out",
                    "ring_id": ring_id,
                }
            )

    # Pass-through chains
    chain_groups = []
    for c in range(n_chains):
        ring_id = f"CHAIN-{c+1:03d}"
        c_accs = chain_ids[c * 6 : (c + 1) * 6]
        chain_groups.append((ring_id, c_accs))
        for c_id in c_accs:
            age = float(rng.uniform(15.0, 500.0))
            account_rows.append(
                {
                    "account_id": c_id,
                    "account_age_days": round(age, 1),
                    "is_fraud": 1,
                    "typology": "pass_through_chain",
                    "ring_id": ring_id,
                }
            )

    # Burst velocity accounts
    for b_id in burst_ids:
        age = float(rng.uniform(100.0, 1500.0))
        account_rows.append(
            {
                "account_id": b_id,
                "account_age_days": round(age, 1),
                "is_fraud": 1,
                "typology": "burst_velocity",
                "ring_id": "",
            }
        )

    # Normal accounts
    for norm_id in normal_ids:
        age = float(rng.uniform(NORMAL_AGE_MIN_DAYS, NORMAL_AGE_MAX_DAYS))
        account_rows.append(
            {
                "account_id": norm_id,
                "account_age_days": round(age, 1),
                "is_fraud": 0,
                "typology": "",
                "ring_id": "",
            }
        )

    accounts_truth = pd.DataFrame(account_rows)
    # Sort accounts deterministically by account_id
    accounts_truth.sort_values(by="account_id", inplace=True)
    accounts_truth.reset_index(drop=True, inplace=True)

    # 3. Simulate Transactions
    transactions = []

    def random_daytime_ts(day_idx: int) -> datetime:
        hour = rng.integers(6, 23)
        minute = rng.integers(0, 60)
        second = rng.integers(0, 60)
        return base_start_time + timedelta(
            days=int(day_idx), hours=int(hour), minutes=int(minute), seconds=int(second)
        )

    # Realistic background activity across ALL accounts (including fraud mules & chains)
    # This prevents fraud accounts from having an artificial signature like txn_count_out == 1.
    for aid in all_account_ids:
        n_bg = rng.integers(3, 10)
        peers = rng.choice(ordinary_ids, size=min(4, len(ordinary_ids)), replace=False)
        for _ in range(n_bg):
            b_day = rng.integers(0, days)
            b_ts = random_daytime_ts(b_day)
            peer = rng.choice(peers)
            if peer == aid:
                continue
            amt = round(float(rng.uniform(150.0, 3000.0)), 2)
            if rng.random() < 0.6:
                transactions.append(
                    {
                        "timestamp": b_ts,
                        "sender_id": aid,
                        "receiver_id": peer,
                        "amount_inr": amt,
                        "typology": "",
                    }
                )
            else:
                transactions.append(
                    {
                        "timestamp": b_ts,
                        "sender_id": peer,
                        "receiver_id": aid,
                        "amount_inr": amt,
                        "typology": "",
                    }
                )

    # A. Fan-in Fan-out Fraud Rings
    for ring_id, collector_id, mule_ids in fan_in_ring_groups:
        ring_day = rng.integers(1, max(2, days - 2))
        for mule_id in mule_ids:
            # Mule receives payments (overlapping merchant range: 10-30 payments)
            n_in_txns = rng.integers(10, 26)
            senders = rng.choice(ordinary_ids, size=n_in_txns, replace=False)

            mule_start_hour = rng.integers(8, 18)
            mule_start_min = rng.integers(0, 45)
            mule_start_ts = base_start_time + timedelta(
                days=int(ring_day), hours=int(mule_start_hour), minutes=int(mule_start_min)
            )

            total_received = 0.0
            last_in_ts = mule_start_ts

            for i, sender_id in enumerate(senders):
                offset_sec = i * rng.integers(40, 240) + rng.integers(5, 30)
                txn_ts = mule_start_ts + timedelta(seconds=int(offset_sec))
                last_in_ts = txn_ts
                amt = round(float(rng.uniform(FAN_IN_AMOUNT_MIN_INR, FAN_IN_AMOUNT_MAX_INR)), 2)
                total_received += amt
                transactions.append(
                    {
                        "timestamp": txn_ts,
                        "sender_id": sender_id,
                        "receiver_id": mule_id,
                        "amount_inr": amt,
                        "typology": "fan_in_fan_out",
                    }
                )

            # Mule forwards to collector with timing noise
            speed_roll = rng.random()
            if speed_roll < 0.40:
                fwd_delay_min = rng.uniform(3.0, 20.0)
            elif speed_roll < 0.70:
                fwd_delay_min = rng.uniform(25.0, 75.0)
            else:
                fwd_delay_min = rng.uniform(80.0, 240.0)

            fwd_ratio = rng.uniform(0.65, 0.95)
            fwd_amt = round(float(total_received * fwd_ratio), 2)
            fwd_ts = last_in_ts + timedelta(minutes=float(fwd_delay_min))
            transactions.append(
                {
                    "timestamp": fwd_ts,
                    "sender_id": mule_id,
                    "receiver_id": collector_id,
                    "amount_inr": fwd_amt,
                    "typology": "fan_in_fan_out",
                }
            )

    # B. Pass-through Chain Transactions
    for ring_id, c_accs in chain_groups:
        chain_day = rng.integers(1, max(2, days - 2))
        entry_acc = c_accs[0]
        n_senders = rng.integers(PASS_THROUGH_SENDERS_MIN, PASS_THROUGH_SENDERS_MAX + 1)
        senders = rng.choice(ordinary_ids, size=n_senders, replace=False)
        chain_start_ts = base_start_time + timedelta(
            days=int(chain_day), hours=int(rng.integers(8, 16)), minutes=int(rng.integers(0, 30))
        )

        total_chain_in = 0.0
        cur_ts = chain_start_ts
        for i, sender_id in enumerate(senders):
            in_ts = chain_start_ts + timedelta(minutes=int(i * 4 + rng.integers(1, 4)))
            cur_ts = in_ts
            in_amt = round(float(rng.uniform(5000.0, 22000.0)), 2)
            total_chain_in += in_amt
            transactions.append(
                {
                    "timestamp": in_ts,
                    "sender_id": sender_id,
                    "receiver_id": entry_acc,
                    "amount_inr": in_amt,
                    "typology": "pass_through_chain",
                }
            )

        cur_amt = total_chain_in
        for hop_idx in range(len(c_accs) - 1):
            src = c_accs[hop_idx]
            dst = c_accs[hop_idx + 1]
            if rng.random() < 0.25:
                hop_delay = rng.uniform(35.0, 120.0)
            else:
                hop_delay = rng.uniform(4.0, 22.0)
            cur_ts = cur_ts + timedelta(minutes=float(hop_delay))
            fee = PASS_THROUGH_FEE_RATIO + rng.uniform(-0.015, 0.015)
            cur_amt = round(float(cur_amt * (1.0 - fee)), 2)
            transactions.append(
                {
                    "timestamp": cur_ts,
                    "sender_id": src,
                    "receiver_id": dst,
                    "amount_inr": cur_amt,
                    "typology": "pass_through_chain",
                }
            )

    # C. Burst Velocity Transactions
    for b_id in burst_ids:
        burst_day = rng.integers(1, max(2, days - 2))
        burst_hour = rng.integers(0, 5)  # 00:00 to 04:59
        burst_min = rng.integers(0, 48)
        burst_sec = rng.integers(0, 60)
        burst_start_ts = base_start_time + timedelta(
            days=int(burst_day), hours=int(burst_hour), minutes=int(burst_min), seconds=int(burst_sec)
        )

        n_burst_txns = rng.integers(BURST_VELOCITY_OUT_TXNS_MIN, BURST_VELOCITY_OUT_TXNS_MAX + 1)
        n_receivers = rng.integers(
            BURST_VELOCITY_RECEIVERS_MIN,
            min(n_burst_txns, BURST_VELOCITY_RECEIVERS_MAX) + 1,
        )
        recvs_pool = rng.choice(ordinary_ids, size=n_receivers, replace=False)
        assigned_recvs = rng.choice(recvs_pool, size=n_burst_txns, replace=True)

        offsets = np.sort(rng.uniform(0.0, 570.0, size=n_burst_txns))
        for off, r_id in zip(offsets, assigned_recvs):
            t_ts = burst_start_ts + timedelta(seconds=float(off))
            amt = round(float(rng.uniform(BURST_VELOCITY_AMOUNT_MIN_INR, BURST_VELOCITY_AMOUNT_MAX_INR)), 2)
            transactions.append(
                {
                    "timestamp": t_ts,
                    "sender_id": b_id,
                    "receiver_id": r_id,
                    "amount_inr": amt,
                    "typology": "burst_velocity",
                }
            )

    # D. Normal Accounts Transactions
    # 1. Ordinary Accounts
    for ord_id in ordinary_ids:
        n_txns = rng.integers(2, 16)
        n_peers = rng.integers(1, min(7, len(ordinary_ids)))
        peers = rng.choice(ordinary_ids, size=n_peers, replace=False)
        for _ in range(n_txns):
            t_day = rng.integers(0, days)
            t_ts = random_daytime_ts(t_day)
            peer = rng.choice(peers)
            if peer == ord_id:
                continue
            raw_amt = float(rng.lognormal(mean=np.log(800.0), sigma=0.6))
            amt = round(float(np.clip(raw_amt, 50.0, 35000.0)), 2)
            transactions.append(
                {
                    "timestamp": t_ts,
                    "sender_id": ord_id,
                    "receiver_id": peer,
                    "amount_inr": amt,
                    "typology": "",
                }
            )

    # 2. Merchants (Hard Negatives for Fan-In): receive 20-80 txns, but 30% of merchants forward 15-35% of funds to suppliers!
    for m_id in merchant_ids:
        n_customers = rng.integers(20, min(81, len(ordinary_ids)))
        customers = rng.choice(ordinary_ids, size=n_customers, replace=False)
        total_m_in = 0.0
        for cust_id in customers:
            t_day = rng.integers(0, days)
            t_ts = random_daytime_ts(t_day)
            amt = round(float(rng.uniform(200.0, 6000.0)), 2)
            total_m_in += amt
            transactions.append(
                {
                    "timestamp": t_ts,
                    "sender_id": cust_id,
                    "receiver_id": m_id,
                    "amount_inr": amt,
                    "typology": "",
                }
            )

        # Forwarding to suppliers/distributors
        if rng.random() < 0.40 and total_m_in > 500.0:
            n_fwd = rng.integers(1, 5)
            fwd_ratio = rng.uniform(0.10, 0.35)
            fwd_total = total_m_in * fwd_ratio
            fwd_peers = rng.choice(ordinary_ids, size=n_fwd, replace=False)
            for f_peer in fwd_peers:
                t_day = rng.integers(1, days)
                t_ts = random_daytime_ts(t_day)
                fwd_amt = round(float(fwd_total / n_fwd), 2)
                transactions.append(
                    {
                        "timestamp": t_ts,
                        "sender_id": m_id,
                        "receiver_id": f_peer,
                        "amount_inr": fwd_amt,
                        "typology": "",
                    }
                )

    # 3. Payroll accounts: funding deposit -> holds -> pays 10-40 employees
    for p_id in payroll_ids:
        n_cycles = rng.integers(1, 3)
        for cycle in range(n_cycles):
            c_day = rng.integers(0, max(1, days - 2))
            c_ts = random_daytime_ts(c_day)
            funding_src = rng.choice(ordinary_ids)
            funding_amt = round(float(rng.uniform(150000.0, 450000.0)), 2)
            transactions.append(
                {
                    "timestamp": c_ts,
                    "sender_id": funding_src,
                    "receiver_id": p_id,
                    "amount_inr": funding_amt,
                    "typology": "",
                }
            )

            n_employees = rng.integers(10, min(41, len(ordinary_ids)))
            employees = rng.choice(ordinary_ids, size=n_employees, replace=False)
            disburse_ts = c_ts + timedelta(hours=int(rng.integers(12, 48)))
            emp_amt = round(float(funding_amt * 0.90 / n_employees), 2)
            for i, emp_id in enumerate(employees):
                e_ts = disburse_ts + timedelta(seconds=int(i * 30 + rng.integers(5, 15)))
                transactions.append(
                    {
                        "timestamp": e_ts,
                        "sender_id": p_id,
                        "receiver_id": emp_id,
                        "amount_inr": emp_amt,
                        "typology": "",
                    }
                )

    # 4. Aggregators (Hard Negatives for Forwarding Speed & Forward Ratio):
    # Receive funds in daytime and forward 85-98% within 3-15 minutes
    for agg_id in aggregator_ids:
        n_batches = rng.integers(15, 35)
        for _ in range(n_batches):
            b_day = rng.integers(0, days)
            b_hour = rng.integers(8, 20)
            b_min = rng.integers(0, 50)
            in_ts = base_start_time + timedelta(
                days=int(b_day), hours=int(b_hour), minutes=int(b_min), seconds=int(rng.integers(0, 60))
            )
            src_user = rng.choice(ordinary_ids)
            in_amt = round(float(rng.uniform(1500.0, 16000.0)), 2)
            transactions.append(
                {
                    "timestamp": in_ts,
                    "sender_id": src_user,
                    "receiver_id": agg_id,
                    "amount_inr": in_amt,
                    "typology": "",
                }
            )

            # Fast forward within 3-15 minutes
            fwd_ts = in_ts + timedelta(minutes=float(rng.uniform(3.0, 15.0)))
            dst_user = rng.choice(ordinary_ids)
            fwd_amt = round(float(in_amt * rng.uniform(0.85, 0.98)), 2)
            transactions.append(
                {
                    "timestamp": fwd_ts,
                    "sender_id": agg_id,
                    "receiver_id": dst_user,
                    "amount_inr": fwd_amt,
                    "typology": "",
                }
            )

    # 5. Night-Active Ordinary Accounts (Hard Negatives for night ratio)
    for n_id in night_active_ids:
        n_txns = rng.integers(3, 16)
        peers = rng.choice(ordinary_ids, size=min(4, len(ordinary_ids)), replace=False)
        for _ in range(n_txns):
            t_day = rng.integers(0, days)
            t_hour = rng.integers(0, 5)
            t_min = rng.integers(0, 60)
            t_sec = rng.integers(0, 60)
            t_ts = base_start_time + timedelta(
                days=int(t_day), hours=int(t_hour), minutes=int(t_min), seconds=int(t_sec)
            )
            peer = rng.choice(peers)
            raw_amt = float(rng.lognormal(mean=np.log(800.0), sigma=0.6))
            amt = round(float(np.clip(raw_amt, 50.0, 25000.0)), 2)
            transactions.append(
                {
                    "timestamp": t_ts,
                    "sender_id": n_id,
                    "receiver_id": peer,
                    "amount_inr": amt,
                    "typology": "",
                }
            )

    # 6. Family / Peer Expense Poolers (Hard Negatives for Mule Fan-In & Fast Forwarding):
    # Ordinary user receives money from 4 to 10 friends/family and forwards 80-95% within 10-45 minutes.
    for pooler_id in pooler_ids:
        p_day = rng.integers(1, max(2, days - 2))
        p_hour = rng.integers(9, 19)
        p_start_ts = base_start_time + timedelta(
            days=int(p_day), hours=int(p_hour), minutes=int(rng.integers(0, 45))
        )
        n_contributors = rng.integers(4, 11)
        contributors = rng.choice(ordinary_ids, size=n_contributors, replace=False)
        total_pooled = 0.0
        last_pool_ts = p_start_ts
        for i, c_id in enumerate(contributors):
            c_ts = p_start_ts + timedelta(minutes=int(i * 3 + rng.integers(1, 5)))
            last_pool_ts = c_ts
            c_amt = round(float(rng.uniform(1000.0, 8000.0)), 2)
            total_pooled += c_amt
            transactions.append(
                {
                    "timestamp": c_ts,
                    "sender_id": c_id,
                    "receiver_id": pooler_id,
                    "amount_inr": c_amt,
                    "typology": "",
                }
            )

        # Forward pooled money to merchant or landlord
        pool_fwd_ts = last_pool_ts + timedelta(minutes=float(rng.uniform(8.0, 40.0)))
        pool_dst = rng.choice(ordinary_ids)
        pool_fwd_amt = round(float(total_pooled * rng.uniform(0.85, 0.98)), 2)
        transactions.append(
            {
                "timestamp": pool_fwd_ts,
                "sender_id": pooler_id,
                "receiver_id": pool_dst,
                "amount_inr": pool_fwd_amt,
                "typology": "",
            }
        )

    # 4. Finalize DataFrame
    df_txns = pd.DataFrame(transactions)
    df_txns["timestamp"] = pd.to_datetime(df_txns["timestamp"])
    df_txns.sort_values(by=["timestamp", "sender_id", "receiver_id"], inplace=True)
    df_txns.reset_index(drop=True, inplace=True)
    df_txns.insert(0, "txn_id", [f"TXN-{i+1:06d}" for i in range(len(df_txns))])

    df_txns = df_txns[
        ["txn_id", "timestamp", "sender_id", "receiver_id", "amount_inr", "typology"]
    ]

    return accounts_truth, df_txns
