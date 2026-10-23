import React from 'react';

/**
 * AlertTable Component
 *
 * Props:
 * - alerts (Array<object>): List of alert items [{ rank, account_id, risk_score, top_reason, ground_truth_fraud, true_typology }]
 * - selectedAccountId (string|null): Currently selected account ID
 * - onSelectAccount (function): Callback when an account alert row is clicked
 */
export default function AlertTable({ alerts = [], selectedAccountId = null, onSelectAccount = () => {} }) {
  return (
    <div className="alert-table-placeholder" data-testid="alert-table">
      <h3>Ranked Alerts ({alerts.length})</h3>
    </div>
  );
}
