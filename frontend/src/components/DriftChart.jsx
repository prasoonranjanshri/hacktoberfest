import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function DriftChart({ driftData = null }) {
  // Render only if /api/drift returns available: true per spec
  if (!driftData || !driftData.available) {
    return null;
  }

  const windows = driftData.windows || [];

  return (
    <div className="card">
      <div className="card-title">
        <span>Model & Data Drift Monitoring</span>
        <span className="badge badge-fixture">PSI Alert Threshold: {driftData.psi_alert_threshold ?? 0.2}</span>
      </div>

      {driftData.note && (
        <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "12px" }}>
          {driftData.note}
        </div>
      )}

      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={windows} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="window" stroke="#64748b" tick={{ fill: "#94a3b8", fontSize: 12 }} />
            <YAxis stroke="#64748b" tick={{ fill: "#94a3b8", fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0f172a",
                borderColor: "#334155",
                borderRadius: "8px",
                fontSize: "12px",
                color: "#f8fafc",
              }}
            />
            <Legend wrapperStyle={{ fontSize: "12px" }} />
            <Bar dataKey="psi" name="Population Stability Index (PSI)" fill="#f59e0b" />
            <Bar dataKey="recall_frozen" name="Recall (Frozen Model)" fill="#ef4444" />
            <Bar dataKey="recall_retrained" name="Recall (Retrained)" fill="#10b981" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
