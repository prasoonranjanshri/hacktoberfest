import React, { useState } from 'react';
import Header from './components/Header';
import SummaryCards from './components/SummaryCards';
import BudgetControl from './components/BudgetControl';
import AlertTable from './components/AlertTable';
import AccountDetail from './components/AccountDetail';
import NetworkGraph from './components/NetworkGraph';
import BudgetCurveChart from './components/BudgetCurveChart';
import DriftChart from './components/DriftChart';
import ErrorBanner from './components/ErrorBanner';

export default function App() {
  const [budget, setBudget] = useState(100);
  const [selectedAccountId, setSelectedAccountId] = useState(null);
  const [error, setError] = useState(null);

  return (
    <div className="mulenet-app">
      <Header dataSource="sample_fixture" generatedAt="2026-09-30T23:59:59" version="1.0.0" />
      <ErrorBanner error={error} onRetry={() => setError(null)} />
      <main style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <SummaryCards dataset={{}} model={{}} />
        <BudgetControl budget={budget} onBudgetChange={setBudget} min={1} max={1000} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          <AlertTable alerts={[]} selectedAccountId={selectedAccountId} onSelectAccount={setSelectedAccountId} />
          <AccountDetail account={null} loading={false} />
        </div>
        <NetworkGraph graphData={null} centerId={selectedAccountId} onNodeClick={(id) => setSelectedAccountId(id)} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          <BudgetCurveChart curveData={null} currentBudget={budget} />
          <DriftChart driftData={null} />
        </div>
      </main>
    </div>
  );
}
