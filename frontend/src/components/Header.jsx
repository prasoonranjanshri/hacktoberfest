import React from 'react';

/**
 * Header Component
 *
 * Props:
 * - dataSource (string): Data source identifier (e.g., 'sample_fixture', 'synthetic_pipeline')
 * - generatedAt (string): ISO timestamp when artifacts were produced
 * - version (string): API / System version
 */
export default function Header({ dataSource = 'sample_fixture', generatedAt = '', version = '1.0.0' }) {
  return (
    <header className="header-placeholder" data-testid="header">
      <h1>MuleNet</h1>
      <span className="badge">{dataSource ? dataSource.toUpperCase() : 'SYNTHETIC'}</span>
      <span className="version">v{version}</span>
    </header>
  );
}
