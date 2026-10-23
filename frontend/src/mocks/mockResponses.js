/**
 * Contract-shaped mock fixtures for MuleNet frontend offline testing.
 */

export const mockHealth = {
  status: "ok",
  service: "mulenet-api",
  version: "1.0.0",
  artifacts_loaded: true,
  data_source: "mock_mode",
  generated_at: "2026-10-23T12:00:00",
};

export const mockSummary = {
  data_source: "mock_mode",
  generated_at: "2026-10-23T12:00:00",
  seed: 42,
  dataset: {
    n_accounts: 3000,
    n_transactions: 34500,
    n_fraud_accounts: 150,
    fraud_rate: 0.05,
    typology_counts: {
      fan_in_fan_out: 60,
      pass_through_chain: 48,
      burst_velocity: 42,
    },
  },
  model: {
    name: "xgboost",
    cv_scheme: "GroupKFold",
    cv_splits: 5,
    pr_auc: 0.9995,
    pr_auc_behaviour_only: 0.9996,
  },
};

export function getMockAlerts(budget = 100) {
  const alerts = [];
  const limit = Math.min(budget, 150);
  for (let i = 1; i <= limit; i++) {
    const aid = `ACC-${String(i).padStart(5, "0")}`;
    const isFraud = i <= 150;
    const typo =
      i <= 60
        ? "fan_in_fan_out"
        : i <= 108
        ? "pass_through_chain"
        : "burst_velocity";
    alerts.push({
      rank: i,
      account_id: aid,
      risk_score: Number((1.0 - i * 0.001).toFixed(4)),
      top_reason:
        i <= 60
          ? "Forwarded 92% of received money within 15 minutes"
          : i <= 108
          ? "Typically moves money out 8 minutes after receiving it"
          : "Made up to 24 payments within 10 minutes",
      ground_truth_fraud: isFraud,
      true_typology: typo,
    });
  }

  const trueCaught = Math.min(budget, 150);
  const falseAlerts = Math.max(0, budget - trueCaught);

  return {
    budget: budget,
    budget_summary: {
      alerts_returned: budget,
      true_frauds_caught: trueCaught,
      false_alerts: falseAlerts,
      total_frauds: 150,
      recall: Number((trueCaught / 150).toFixed(4)),
      precision: Number((trueCaught / budget).toFixed(4)),
      false_alerts_per_1000_accounts: Number(
        ((falseAlerts / 3000) * 1000).toFixed(4)
      ),
      behaviour_only_true_frauds_caught: Math.min(budget, 148),
    },
    alerts: alerts,
  };
}

export const mockAccountDetails = {
  "ACC-00004": {
    account_id: "ACC-00004",
    rank: 1,
    risk_score: 0.9998,
    baseline_score: 0.9998,
    ground_truth_fraud: true,
    true_typology: "fan_in_fan_out",
    ring_id: "RING-001",
    reasons: [
      {
        feature: "txn_count_out",
        text: "Sent 1 payments",
        shap: 7.7695,
        value: 1.0,
      },
      {
        feature: "total_out_inr",
        text: "Sent a total of INR 72,764",
        shap: 1.0273,
        value: 72763.94,
      },
      {
        feature: "median_hold_minutes",
        text: "Typically moves money out 124 minutes after receiving it",
        shap: 0.4295,
        value: 124.24,
      },
    ],
    features: {
      txn_count_out: 1.0,
      txn_count_in: 6.0,
      total_out_inr: 72763.94,
      total_in_inr: 79332.82,
      avg_amount_out: 72763.94,
      night_txn_ratio: 0.0,
      new_payee_ratio: 1.0,
      max_out_txns_10min: 1.0,
      account_age_days: 46.9,
      n_unique_senders: 6.0,
      n_unique_receivers: 1.0,
      forward_ratio_15min: 0.0,
      median_hold_minutes: 124.24,
      neighbour_mean_forward_ratio: 0.0,
    },
  },
};

export const mockGraph = {
  center_id: "ACC-00004",
  hops: 1,
  truncated: false,
  nodes: [
    {
      id: "ACC-00004",
      risk_score: 0.9998,
      ground_truth_fraud: true,
      is_center: true,
    },
    {
      id: "ACC-00001",
      risk_score: 0.9981,
      ground_truth_fraud: true,
      is_center: false,
    },
    {
      id: "ACC-00153",
      risk_score: 0.0125,
      ground_truth_fraud: false,
      is_center: false,
    },
    {
      id: "ACC-00154",
      risk_score: 0.021,
      ground_truth_fraud: false,
      is_center: false,
    },
  ],
  edges: [
    {
      source: "ACC-00004",
      target: "ACC-00001",
      txn_count: 1,
      total_amount_inr: 72763.94,
      first_ts: "2026-09-20T12:29:56",
      last_ts: "2026-09-20T12:29:56",
    },
    {
      source: "ACC-00153",
      target: "ACC-00004",
      txn_count: 1,
      total_amount_inr: 18443.26,
      first_ts: "2026-09-20T10:30:14",
      last_ts: "2026-09-20T10:30:14",
    },
    {
      source: "ACC-00154",
      target: "ACC-00004",
      txn_count: 1,
      total_amount_inr: 15200.0,
      first_ts: "2026-09-20T10:35:00",
      last_ts: "2026-09-20T10:35:00",
    },
  ],
};

export const mockBudgetCurve = {
  budgets: [10, 20, 30, 40, 50, 100, 150, 200, 250, 300],
  total_frauds: 150,
  total_accounts: 3000,
  full: {
    true_frauds_caught: [10, 20, 30, 40, 50, 100, 148, 150, 150, 150],
    false_alerts: [0, 0, 0, 0, 0, 0, 2, 50, 100, 150],
    recall: [0.0667, 0.1333, 0.2, 0.2667, 0.3333, 0.6667, 0.9867, 1.0, 1.0, 1.0],
  },
  behaviour_only: {
    true_frauds_caught: [10, 20, 30, 40, 50, 100, 146, 149, 150, 150],
    false_alerts: [0, 0, 0, 0, 0, 0, 4, 51, 100, 150],
    recall: [0.0667, 0.1333, 0.2, 0.2667, 0.3333, 0.6667, 0.9733, 0.9933, 1.0, 1.0],
  },
};

export const mockDrift = {
  available: false,
};

export default {
  mockHealth,
  mockSummary,
  getMockAlerts,
  mockAccountDetails,
  mockGraph,
  mockBudgetCurve,
  mockDrift,
};
