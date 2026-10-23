import React from 'react';

/**
 * ErrorBanner Component
 *
 * Props:
 * - error (object|string|null): Error details or message
 * - onRetry (function): Callback to retry failed action
 */
export default function ErrorBanner({ error = null, onRetry = () => {} }) {
  if (!error) return null;

  const errorMessage =
    typeof error === 'string'
      ? error
      : error?.message || error?.error?.message || 'A network or server error occurred.';

  return (
    <div className="error-banner" data-testid="error-banner" style={{ background: '#ef4444', color: '#fff', padding: '12px' }}>
      <span>{errorMessage}</span>
      <button onClick={onRetry} style={{ marginLeft: '12px' }}>Retry</button>
    </div>
  );
}
