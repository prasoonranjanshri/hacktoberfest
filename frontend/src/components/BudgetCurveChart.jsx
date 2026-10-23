import React from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function BudgetCurveChart({
  curveData = null,
  currentBudget = 100,
  loading = false,
}) {
  if (loading) {
    return (
      <div className="card">
        <div className="card-title">Budget Sensitivity Curve (Ablation)</div>
        <div className="skeleton" style={{ height: "300px", width: "100%" }} />
      </div>
    );
  }

  // Format data for Recharts
  const chartData = [];
  if (curveData && curveData.budgets) {
    const { budgets, full, behaviour_only } = curveData;
    for (let i = 0; i < budgets.length; i++) {
      chartData.push({
        budget: budgets[i],
        fullRecall: full?.recall ? Number((full.recall[i] * 100).toFixed(1)) : 0,
        fullCaught: full?.true_frauds_caught ? full.true_frauds_caught[i] : 0,
        behRecall: behaviour_only?.recall
          ? Number((behaviour_only.recall[i] * 100).toFixed(1))
          : 0,
        behCaught: behaviour_only?.true_frauds_caught
          ? behaviour_only.true_frauds_caught[i]
          : 0,
      });
    }
  }

  return (
    <div className="card">
      <div className="card-title">
        <div>
          <span>Budget Sensitivity Curve</span>
          <span style={{ fontSize: "12px", color: "var(--text-muted)", marginLeft: "8px" }}>
            Full Model vs. Behaviour-Only Ablation
          </span>
        </div>
        <span className="ground-truth-tag">Demo evaluation (recall vs budget)</span>
      </div>

      <div style={{ width: "100%", height: 300, marginTop: "12px" }}>
        {chartData.length === 0 ? (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--text-muted)" }}>
            No sensitivity curve data available.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey="budget"
                stroke="#64748b"
                tick={{ fill: "#94a3b8", fontSize: 12 }}
                name="Budget"
                unit=""
              />
              <YAxis
                stroke="#64748b"
                tick={{ fill: "#94a3b8", fontSize: 12 }}
                domain={[0, 100]}
                unit="%"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#334155",
                  borderRadius: "8px",
                  fontSize: "12px",
                  color: "#f8fafc",
                }}
                formatter={(val, name) => {
                  if (name === "Full Model Recall") return [`${val}%`, name];
                  if (name === "Behaviour-Only Recall") return [`${val}%`, name];
                  return [val, name];
                }}
                labelFormatter={(label) => `Investigation Budget: ${label} alerts`}
              />
              <Legend
                wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }}
              />
              <ReferenceLine
                x={currentBudget}
                stroke="#f59e0b"
                strokeDasharray="4 4"
                label={{
                  value: `Current: ${currentBudget}`,
                  fill: "#f59e0b",
                  fontSize: 11,
                  position: "top",
                }}
              />
              <Line
                type="monotone"
                dataKey="fullRecall"
                name="Full Model Recall"
                stroke="#06b6d4"
                strokeWidth={2.5}
                dot={{ r: 3, fill: "#06b6d4" }}
                activeDot={{ r: 6 }}
              />
              <Line
                type="monotone"
                dataKey="behRecall"
                name="Behaviour-Only Recall"
                stroke="#a855f7"
                strokeWidth={2}
                strokeDasharray="4 2"
                dot={{ r: 3, fill: "#a855f7" }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
