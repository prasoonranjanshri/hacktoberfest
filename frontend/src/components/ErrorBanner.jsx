import React from "react";

export default function ErrorBanner({ error = null, onRetry }) {
  if (!error) return null;

  const is503 = error.status === 503 || error.code === "ARTIFACTS_NOT_FOUND";
  const isNetwork = error.code === "NETWORK_ERROR";

  const message = error.message || "An unexpected error occurred.";
  const details =
    error.details && error.details.errors
      ? Array.isArray(error.details.errors)
        ? error.details.errors.join("; ")
        : JSON.stringify(error.details.errors)
      : null;

  return (
    <div className={isNetwork ? "offline-banner" : "error-banner"} style={{ margin: "16px 24px 0" }}>
      <div>
        <div style={{ fontWeight: 600, display: "flex", alignItems: "center", gap: "8px" }}>
          <span>{isNetwork ? "Backend Connection Offline" : is503 ? "Artifacts Missing (503)" : `Error [${error.code || "UNKNOWN"}]`}</span>
        </div>
        <div style={{ marginTop: "4px", fontSize: "12px", opacity: 0.9 }}>
          {message}
          {details && <div style={{ marginTop: "4px", fontFamily: "monospace" }}>{details}</div>}
        </div>
      </div>
      {onRetry && (
        <button className="retry-btn" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
