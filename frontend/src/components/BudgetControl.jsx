import React from 'react';

/**
 * BudgetControl Component
 *
 * Props:
 * - budget (number): Current alert budget value
 * - onBudgetChange (function): Callback when user adjusts budget slider/input
 * - min (number): Minimum allowable budget
 * - max (number): Maximum allowable budget
 */
export default function BudgetControl({ budget = 100, onBudgetChange = () => {}, min = 1, max = 1000 }) {
  return (
    <div className="budget-control-placeholder" data-testid="budget-control">
      <label>Alert Budget: {budget}</label>
      <input
        type="range"
        min={min}
        max={max}
        value={budget}
        onChange={(e) => onBudgetChange(Number(e.target.value))}
      />
    </div>
  );
}
