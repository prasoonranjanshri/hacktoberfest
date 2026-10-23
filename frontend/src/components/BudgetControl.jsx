import React, { useEffect, useState } from "react";

export default function BudgetControl({
  budget = 100,
  onBudgetChange,
  budgetSummary = null,
  min = 10,
  max = 300,
  loading = false,
}) {
  const [sliderVal, setSliderVal] = useState(budget);

  // Sync external budget changes
  useEffect(() => {
    setSliderVal(budget);
  }, [budget]);

  // Debounce 250ms when slider changes
  useEffect(() => {
    const timer = setTimeout(() => {
      if (sliderVal !== budget && onBudgetChange) {
        onBudgetChange(sliderVal);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [sliderVal, budget, onBudgetChange]);

  const caught = budgetSummary?.true_frauds_caught ?? 0;
  const falseAlerts = budgetSummary?.false_alerts ?? 0;
  const recallPct =
    budgetSummary?.recall !== undefined
      ? (budgetSummary.recall * 100).toFixed(1) + "%"
      : "—";
  const precisionPct =
    budgetSummary?.precision !== undefined
      ? (budgetSummary.precision * 100).toFixed(1) + "%"
      : "—";
  const faPer1000 =
    budgetSummary?.false_alerts_per_1000_accounts !== undefined
      ? budgetSummary.false_alerts_per_1000_accounts.toFixed(1)
      : "0.0";
  const behCaught = budgetSummary?.behaviour_only_true_frauds_caught ?? caught;
  const diffFrauds = caught - behCaught;

  return (
    <div className="card budget-control-container">
      <div className="card-title">
        <span>Investigation Alert Budget</span>
        <span className="ground-truth-tag">Demo evaluation (ground truth metrics)</span>
      </div>

      <div className="slider-wrapper">
        <label htmlFor="budget-slider" style={{ fontSize: "13px", color: "var(--text-secondary)", minWidth: "120px" }}>
          Target Budget:
        </label>
        <input
          id="budget-slider"
          type="range"
          min={min}
          max={max}
          step={10}
          value={sliderVal}
          onChange={(e) => setSliderVal(Number(e.target.value))}
          className="budget-slider"
        />
        <div className="budget-val-badge">{sliderVal} alerts</div>
      </div>

      {loading ? (
        <div className="skeleton" style={{ height: "64px", marginTop: "8px" }} />
      ) : (
        <div className="budget-stats-grid">
          <div className="budget-stat-box">
            <div className="stat-label">Frauds Caught</div>
            <div className="stat-val" style={{ color: "var(--accent-emerald)" }}>
              {caught}
            </div>
          </div>

          <div className="budget-stat-box">
            <div className="stat-label">False Alerts</div>
            <div className="stat-val" style={{ color: falseAlerts > 0 ? "var(--risk-med)" : "var(--text-secondary)" }}>
              {falseAlerts}
            </div>
          </div>

          <div className="budget-stat-box">
            <div className="stat-label">Recall</div>
            <div className="stat-val" style={{ color: "var(--accent-cyan)" }}>
              {recallPct}
            </div>
          </div>

          <div className="budget-stat-box">
            <div className="stat-label">Precision</div>
            <div className="stat-val">{precisionPct}</div>
          </div>

          <div className="budget-stat-box">
            <div className="stat-label">False / 1k Accs</div>
            <div className="stat-val">{faPer1000}</div>
          </div>

          <div className="budget-stat-box">
            <div className="stat-label">Advantage vs Baseline</div>
            <div className="stat-val" style={{ color: diffFrauds >= 0 ? "var(--accent-emerald)" : "var(--risk-med)" }}>
              {diffFrauds >= 0 ? `+${diffFrauds}` : diffFrauds} frauds
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
