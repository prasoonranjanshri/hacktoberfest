import React from 'react';

/**
 * SummaryCards Component
 *
 * Props:
 * - dataset (object): { n_accounts, n_transactions, n_fraud_accounts, fraud_rate, typology_counts }
 * - model (object): { name, cv_scheme, cv_splits, pr_auc, pr_auc_behaviour_only }
 */
export default function SummaryCards({ dataset = {}, model = {} }) {
  return (
    <div className="summary-cards-placeholder" data-testid="summary-cards">
      <h3>Summary Metrics</h3>
    </div>
  );
}
