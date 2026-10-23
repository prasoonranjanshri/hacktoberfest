import React from "react";

export default function AccountDetail({ account = null, loading = false }) {
  if (loading) {
    return (
      <div className="card">
        <div className="card-title">Account Investigation Detail</div>
        <div className="skeleton" style={{ height: "350px", width: "100%" }} />
      </div>
    );
  }

  if (!account) {
    return (
      <div className="card" style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "350px", color: "var(--text-muted)" }}>
        Select an alert from the table or click a node in the network graph to inspect details.
      </div>
    );
  }

  const {
    account_id,
    rank,
    risk_score,
    baseline_score,
    ground_truth_fraud,
    true_typology,
    ring_id,
    reasons = [],
    features = {},
  } = account;

  const formatFeatureVal = (key, val) => {
    if (val === undefined || val === null) return "—";
    if (key.includes("inr") || key.includes("amount")) {
      return `INR ${Number(val).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
    }
    if (key.includes("ratio")) {
      return `${(Number(val) * 100).toFixed(1)}%`;
    }
    if (key.includes("minutes")) {
      return `${Number(val).toFixed(1)} min`;
    }
    if (key.includes("days")) {
      return `${Number(val).toFixed(0)} days`;
    }
    return Number(val).toLocaleString();
  };

  return (
    <div className="card">
      <div className="card-title">
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span>Account Detail: <strong style={{ color: "var(--accent-cyan)" }}>{account_id}</strong></span>
          <span className="badge badge-status">Rank #{rank}</span>
          {ring_id && <span className="badge badge-fixture">{ring_id}</span>}
        </div>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span className="ground-truth-tag">Demo evaluation (ground truth)</span>
          <span
            style={{
              fontSize: "11px",
              fontWeight: 600,
              color: ground_truth_fraud ? "#f43f5e" : "#10b981",
            }}
          >
            {ground_truth_fraud ? `Fraud (${true_typology || "unspecified"})` : "Legitimate"}
          </span>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", margin: "10px 0" }}>
        <div className="budget-stat-box">
          <div className="stat-label">Full Model Risk Score</div>
          <div className="stat-val" style={{ color: "var(--accent-cyan)" }}>
            {(risk_score ?? 0).toFixed(4)}
          </div>
        </div>
        <div className="budget-stat-box">
          <div className="stat-label">Behaviour-Only Baseline</div>
          <div className="stat-val" style={{ color: "var(--text-secondary)" }}>
            {(baseline_score ?? 0).toFixed(4)}
          </div>
        </div>
      </div>

      <div style={{ marginTop: "16px" }}>
        <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-secondary)" }}>
          Top Contributing Risk Factors (SHAP Explanations)
        </div>
        <div className="detail-reasons-list">
          {reasons.length === 0 ? (
            <div style={{ fontSize: "13px", color: "var(--text-muted)", fontStyle: "italic", padding: "8px" }}>
              No positive risk contribution factors detected for this account.
            </div>
          ) : (
            reasons.map((r, i) => (
              <div key={i} className="reason-item">
                <div style={{ fontWeight: 500, color: "var(--text-primary)" }}>{r.text}</div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                  Feature: <code>{r.feature}</code> | SHAP: +{r.shap.toFixed(4)} | Value: {r.value}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div style={{ marginTop: "16px" }}>
        <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-secondary)" }}>
          Extracted Feature Vector (14 Dimensions)
        </div>
        <div className="features-grid">
          {Object.entries(features).map(([k, v]) => (
            <div key={k} className="feature-box">
              <div className="f-name">{k}</div>
              <div className="f-val">{formatFeatureVal(k, v)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
