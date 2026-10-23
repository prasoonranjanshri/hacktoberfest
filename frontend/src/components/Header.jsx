import React from "react";

export default function Header({
  dataSource = "synthetic_pipeline",
  generatedAt,
  version = "1.0.0",
  isOnline = true,
  isMock = false,
}) {
  const getBadge = () => {
    if (isMock || dataSource === "mock_mode") {
      return <span className="badge badge-mock">MOCK DATA</span>;
    }
    if (dataSource === "synthetic_pipeline") {
      return <span className="badge badge-synthetic">SYNTHETIC</span>;
    }
    if (dataSource === "sample_fixture") {
      return <span className="badge badge-fixture">SAMPLE FIXTURE</span>;
    }
    return <span className="badge badge-status">{dataSource}</span>;
  };

  return (
    <>
      {(isMock || dataSource === "mock_mode") && (
        <div className="mock-banner">
          DEMO MODE: RUNNING ON SYNTHETIC CONTRACT MOCK FIXTURES
        </div>
      )}
      <header className="app-header">
        <div className="header-brand">
          <div className="brand-logo">M</div>
          <div>
            <div className="brand-title">MuleNet</div>
            <div className="brand-tagline">
              UPI Fraud Ring & Mule Network Investigation Console
            </div>
          </div>
        </div>

        <div className="header-meta">
          {getBadge()}
          {generatedAt && (
            <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              Generated: {new Date(generatedAt).toLocaleString()}
            </span>
          )}
          <span className="badge badge-status">v{version}</span>
          <span className="badge badge-status">
            <span
              className={`status-dot ${isOnline ? "online" : "offline"}`}
            />
            {isOnline ? "API Online" : "API Offline"}
          </span>
        </div>
      </header>
    </>
  );
}
