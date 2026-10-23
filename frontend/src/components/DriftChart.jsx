import React from 'react';

/**
 * DriftChart Component
 *
 * Props:
 * - driftData (object|null): Drift analysis data { available, windows, psi_alert_threshold, new_typology_window, note }
 */
export default function DriftChart({ driftData = null }) {
  return (
    <div className="drift-chart-placeholder" data-testid="drift-chart">
      <h3>Model & Data Drift</h3>
    </div>
  );
}
