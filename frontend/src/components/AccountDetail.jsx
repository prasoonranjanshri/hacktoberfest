import React from 'react';

/**
 * AccountDetail Component
 *
 * Props:
 * - account (object|null): Account details { account_id, rank, risk_score, baseline_score, ground_truth_fraud, true_typology, ring_id, reasons, features }
 * - loading (boolean): Whether account details are currently loading
 */
export default function AccountDetail({ account = null, loading = false }) {
  return (
    <div className="account-detail-placeholder" data-testid="account-detail">
      <h3>Account Details {account ? `(${account.account_id})` : ''}</h3>
    </div>
  );
}
