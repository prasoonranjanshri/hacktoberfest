import React, { useEffect } from "react";

export default function AlertTable({
  alerts = [],
  selectedAccountId,
  onSelectAccount,
  loading = false,
}) {
  // Auto-select first alert if none selected or if alerts list changes
  useEffect(() => {
    if (alerts.length > 0) {
      const exists = alerts.some((a) => a.account_id === selectedAccountId);
      if (!exists && onSelectAccount) {
        onSelectAccount(alerts[0].account_id);
      }
    }
  }, [alerts, selectedAccountId, onSelectAccount]);

  if (loading) {
    return (
      <div className="card">
        <div className="card-title">Ranked Priority Alerts</div>
        <div className="skeleton" style={{ height: "350px", width: "100%" }} />
      </div>
    );
  }

  const getRiskColor = (score) => {
    if (score >= 0.8) return "var(--risk-high)";
    if (score >= 0.4) return "var(--risk-med)";
    return "var(--risk-low)";
  };

  const getTypologyBadge = (isFraud, typo) => {
    if (!isFraud) {
      return (
        <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
          Normal
        </span>
      );
    }
    const label = typo ? typo.replace(/_/g, " ") : "fraud";
    return (
      <span
        style={{
          fontSize: "11px",
          color: "#f43f5e",
          background: "rgba(244, 63, 94, 0.15)",
          padding: "2px 6px",
          borderRadius: "4px",
          textTransform: "capitalize",
        }}
      >
        {label}
      </span>
    );
  };

  return (
    <div className="card">
      <div className="card-title">
        <span>Ranked Priority Alerts ({alerts.length})</span>
        <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
          Click row to inspect ego-network
        </span>
      </div>

      <div className="table-container">
        <table className="alert-table">
          <thead>
            <tr>
              <th style={{ width: "50px" }}>#</th>
              <th>Account ID</th>
              <th>Risk Score</th>
              <th>Primary Reason Indicator</th>
              <th>
                <span className="ground-truth-tag" style={{ fontSize: "10px" }}>
                  Demo evaluation (ground truth)
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            {alerts.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: "center", color: "var(--text-muted)", padding: "24px" }}>
                  No alerts returned for current budget.
                </td>
              </tr>
            ) : (
              alerts.map((item) => {
                const isSelected = item.account_id === selectedAccountId;
                const scorePct = Math.round(item.risk_score * 100);
                const barColor = getRiskColor(item.risk_score);

                return (
                  <tr
                    key={item.account_id}
                    className={isSelected ? "selected" : ""}
                    onClick={() => onSelectAccount && onSelectAccount(item.account_id)}
                  >
                    <td style={{ fontWeight: 600, color: "var(--text-muted)" }}>
                      {item.rank}
                    </td>
                    <td style={{ fontWeight: 600, color: isSelected ? "var(--accent-cyan)" : "inherit" }}>
                      {item.account_id}
                    </td>
                    <td>
                      <div className="risk-bar-container">
                        <div className="risk-bar-bg">
                          <div
                            className="risk-bar-fill"
                            style={{
                              width: `${Math.min(100, Math.max(5, scorePct))}%`,
                              backgroundColor: barColor,
                            }}
                          />
                        </div>
                        <span style={{ fontSize: "11px", color: barColor, fontWeight: 600 }}>
                          {(item.risk_score).toFixed(4)}
                        </span>
                      </div>
                    </td>
                    <td style={{ maxWidth: "260px", color: "var(--text-secondary)" }}>
                      {item.top_reason}
                    </td>
                    <td>
                      {getTypologyBadge(item.ground_truth_fraud, item.true_typology)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
