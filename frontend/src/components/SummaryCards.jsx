import React from "react";

export default function SummaryCards({ dataset = {}, model = {}, loading = false }) {
  if (loading) {
    return (
      <div className="summary-grid">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="metric-card skeleton" style={{ height: "96px" }} />
        ))}
      </div>
    );
  }

  const nAccounts = dataset?.n_accounts ?? 0;
  const nTxns = dataset?.n_transactions ?? 0;
  const nFraud = dataset?.n_fraud_accounts ?? 0;
  const fraudRate = dataset?.fraud_rate ? (dataset.fraud_rate * 100).toFixed(1) : "0.0";
  const prAucFull = model?.pr_auc !== undefined ? model.pr_auc.toFixed(4) : "—";
  const prAucBeh =
    model?.pr_auc_behaviour_only !== undefined
      ? model.pr_auc_behaviour_only.toFixed(4)
      : "—";
  const diffPrAuc =
    model?.pr_auc !== undefined && model?.pr_auc_behaviour_only !== undefined
      ? (model.pr_auc - model.pr_auc_behaviour_only).toFixed(4)
      : "0.0000";

  const typologies = dataset?.typology_counts || {};

  return (
    <div className="summary-grid">
      <div className="metric-card">
        <span className="metric-label">Monitored Accounts</span>
        <div className="metric-value">{nAccounts.toLocaleString()}</div>
        <span className="metric-sub">{nTxns.toLocaleString()} transactions analyzed</span>
      </div>

      <div className="metric-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span className="metric-label">Fraud Accounts</span>
          <span className="ground-truth-tag">Demo evaluation (ground truth)</span>
        </div>
        <div className="metric-value">
          {nFraud}{" "}
          <span style={{ fontSize: "14px", fontWeight: "400", color: "var(--text-muted)" }}>
            ({fraudRate}%)
          </span>
        </div>
        <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "4px" }}>
          <span style={{ fontSize: "11px", color: "var(--text-secondary)" }}>
            Rings: {typologies.fan_in_fan_out ?? 0} | Chains: {typologies.pass_through_chain ?? 0} | Bursts: {typologies.burst_velocity ?? 0}
          </span>
        </div>
      </div>

      <div className="metric-card">
        <span className="metric-label">Full Model PR-AUC</span>
        <div className="metric-value" style={{ color: "var(--accent-cyan)" }}>
          {prAucFull}
        </div>
        <span className="metric-sub">
          {model?.name || "XGBoost"} + 5-fold GroupKFold
        </span>
      </div>

      <div className="metric-card">
        <span className="metric-label">Network vs Behaviour-Only</span>
        <div className="metric-value" style={{ color: Number(diffPrAuc) >= 0 ? "var(--accent-emerald)" : "var(--accent-amber)" }}>
          {Number(diffPrAuc) >= 0 ? `+${diffPrAuc}` : diffPrAuc}
        </div>
        <span className="metric-sub">
          Baseline PR-AUC: {prAucBeh}
        </span>
      </div>
    </div>
  );
}
