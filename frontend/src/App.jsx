import React, { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  getAccount,
  getAlerts,
  getBudgetCurve,
  getDrift,
  getGraph,
  getHealth,
  getSummary,
} from "./api/client";
import AccountDetail from "./components/AccountDetail";
import AlertTable from "./components/AlertTable";
import BudgetControl from "./components/BudgetControl";
import BudgetCurveChart from "./components/BudgetCurveChart";
import DriftChart from "./components/DriftChart";
import ErrorBanner from "./components/ErrorBanner";
import Header from "./components/Header";
import NetworkGraph from "./components/NetworkGraph";
import SummaryCards from "./components/SummaryCards";

export default function App() {
  const [budget, setBudget] = useState(100);
  const [selectedAccountId, setSelectedAccountId] = useState(null);

  // Data states
  const [health, setHealth] = useState(null);
  const [summary, setSummary] = useState(null);
  const [alertsData, setAlertsData] = useState(null);
  const [accountDetail, setAccountDetail] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [curveData, setCurveData] = useState(null);
  const [driftData, setDriftData] = useState(null);

  // Loading states
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [loadingAlerts, setLoadingAlerts] = useState(true);
  const [loadingAccount, setLoadingAccount] = useState(false);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [loadingCurve, setLoadingCurve] = useState(true);

  // Errors
  const [globalError, setGlobalError] = useState(null);
  const [accountError, setAccountError] = useState(null);
  const [graphError, setGraphError] = useState(null);

  const isMock = import.meta.env.VITE_USE_MOCKS === "true";

  // Initial load: health, summary, curve, drift
  const fetchInitialData = useCallback(async () => {
    setLoadingHealth(true);
    setLoadingSummary(true);
    setLoadingCurve(true);
    setGlobalError(null);

    try {
      const h = await getHealth();
      setHealth(h);
    } catch (err) {
      setHealth(null);
      setGlobalError(err);
      setLoadingHealth(false);
      setLoadingSummary(false);
      setLoadingAlerts(false);
      setLoadingCurve(false);
      return;
    } finally {
      setLoadingHealth(false);
    }

    // Summary
    try {
      const s = await getSummary();
      setSummary(s);
    } catch (err) {
      setGlobalError(err);
    } finally {
      setLoadingSummary(false);
    }

    // Budget Curve
    try {
      const c = await getBudgetCurve();
      setCurveData(c);
    } catch (err) {
      console.error("Budget curve error:", err);
    } finally {
      setLoadingCurve(false);
    }

    // Drift (optional)
    try {
      const d = await getDrift();
      setDriftData(d);
    } catch {
      setDriftData({ available: false });
    }
  }, []);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  // Alerts load when budget changes
  useEffect(() => {
    let isCancelled = false;
    setLoadingAlerts(true);

    getAlerts({ budget })
      .then((data) => {
        if (!isCancelled) {
          setAlertsData(data);
          // Auto-select first alert if none or not in current list
          if (data.alerts && data.alerts.length > 0) {
            setSelectedAccountId((prev) => {
              const inList = data.alerts.some((a) => a.account_id === prev);
              return inList ? prev : data.alerts[0].account_id;
            });
          }
        }
      })
      .catch((err) => {
        if (!isCancelled) {
          setGlobalError(err);
        }
      })
      .finally(() => {
        if (!isCancelled) {
          setLoadingAlerts(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [budget]);

  // Account details & graph load when selectedAccountId changes
  useEffect(() => {
    if (!selectedAccountId) return;

    let isCancelled = false;
    setLoadingAccount(true);
    setLoadingGraph(true);
    setAccountError(null);
    setGraphError(null);

    getAccount(selectedAccountId)
      .then((acc) => {
        if (!isCancelled) setAccountDetail(acc);
      })
      .catch((err) => {
        if (!isCancelled) setAccountError(err.message);
      })
      .finally(() => {
        if (!isCancelled) setLoadingAccount(false);
      });

    getGraph(selectedAccountId, { hops: 1, maxNodes: 40 })
      .then((g) => {
        if (!isCancelled) setGraphData(g);
      })
      .catch((err) => {
        if (!isCancelled) setGraphError(err.message);
      })
      .finally(() => {
        if (!isCancelled) setLoadingGraph(false);
      });

    return () => {
      isCancelled = true;
    };
  }, [selectedAccountId]);

  return (
    <div className="mulenet-app">
      <Header
        dataSource={health?.data_source || (isMock ? "mock_mode" : "synthetic_pipeline")}
        generatedAt={health?.generated_at}
        version={health?.version || "1.0.0"}
        isOnline={health !== null && !globalError}
        isMock={isMock}
      />

      <ErrorBanner error={globalError} onRetry={fetchInitialData} />

      <main className="app-main">
        {/* 1. Summary Cards */}
        <SummaryCards
          dataset={summary?.dataset}
          model={summary?.model}
          loading={loadingSummary}
        />

        {/* 2. Budget Control */}
        <BudgetControl
          budget={budget}
          onBudgetChange={setBudget}
          budgetSummary={alertsData?.budget_summary}
          min={10}
          max={300}
          loading={loadingAlerts}
        />

        {/* 3. Alerts Table & Account Detail (Split Pane) */}
        <div className="split-pane">
          <AlertTable
            alerts={alertsData?.alerts || []}
            selectedAccountId={selectedAccountId}
            onSelectAccount={setSelectedAccountId}
            loading={loadingAlerts}
          />

          <AccountDetail
            account={accountDetail}
            loading={loadingAccount}
            error={accountError}
          />
        </div>

        {/* 4. Network Ego Graph */}
        <NetworkGraph
          graphData={graphData}
          centerId={selectedAccountId}
          onNodeClick={(id) => setSelectedAccountId(id)}
          loading={loadingGraph}
          error={graphError}
        />

        {/* 5. Budget Curve Chart & Drift Monitoring */}
        <div className="split-pane">
          <BudgetCurveChart
            curveData={curveData}
            currentBudget={budget}
            loading={loadingCurve}
          />

          <DriftChart driftData={driftData} />
        </div>
      </main>

      <footer className="app-footer">
        <div>MuleNet &mdash; Fraud Network & Mule Ring Detection</div>
        <div style={{ marginTop: "4px", color: "var(--text-muted)" }}>
          All data is synthetic. Fraud rate is set to 5% for demonstration; real-world rates are far lower.
        </div>
      </footer>
    </div>
  );
}
