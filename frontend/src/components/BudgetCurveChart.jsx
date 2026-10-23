import React from 'react';

/**
 * BudgetCurveChart Component
 *
 * Props:
 * - curveData (object|null): Budget curve series { budgets, total_frauds, total_accounts, full, behaviour_only }
 * - currentBudget (number): Currently selected budget mark
 */
export default function BudgetCurveChart({ curveData = null, currentBudget = 100 }) {
  return (
    <div className="budget-curve-chart-placeholder" data-testid="budget-curve-chart">
      <h3>Budget Sensitivity Curve</h3>
    </div>
  );
}
