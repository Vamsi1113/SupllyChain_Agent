import React, { useState, useEffect } from 'react';
import { startRun, getStatus, submitApproval } from '../services/api';

import IncidentCard from '../components/IncidentCard';
import StatusTracker from '../components/StatusTracker';
import AgentLogPanel from '../components/AgentLogPanel';
import ApprovalPanel from '../components/ApprovalPanel';
import FinalDecisionPanel from '../components/FinalDecisionPanel';

export default function Dashboard() {
  const [runId, setRunId] = useState(null);
  const [statusData, setStatusData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Poll status every 2s if running
  useEffect(() => {
    let interval;
    if (runId && statusData?.status && ['queued', 'running'].includes(statusData.status)) {
      interval = setInterval(async () => {
        try {
          const data = await getStatus(runId);
          setStatusData(data);
        } catch (err) {
          console.error("Polling error:", err);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [runId, statusData?.status]);

  async function handleIncidentSubmit(payload) {
    setLoading(true);
    setError(null);
    setStatusData(null);
    try {
      const { run_id } = await startRun(payload);
      setRunId(run_id);
      
      // Fetch initial state immediately
      const initial = await getStatus(run_id);
      setStatusData(initial);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleApproval(approved, comments = '') {
    setLoading(true);
    try {
      if (runId) {
        await submitApproval(runId, approved, comments);
        // Immediately clear awaiting status in UI to prevent double submission
        setStatusData(prev => ({
          ...prev,
          status: 'running',
          approval_status: approved ? 'approved' : 'rejected'
        }));
      }
    } catch (err) {
      setError(`Approval failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen p-6 md:p-8 max-w-7xl mx-auto flex flex-col lg:flex-row gap-8">
      
      {/* Left Column: Form & Key Info */}
      <div className="lg:w-1/3 flex flex-col gap-6">
        <header className="mb-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-brand-500 rounded-xl flex items-center justify-center shadow-lg shadow-brand-500/30">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
              Supply Chain AI
            </h1>
          </div>
          <p className="text-slate-400 text-sm">Autonomous disruption orchestration</p>
        </header>

        <IncidentCard onSubmit={handleIncidentSubmit} loading={loading} />

        {error && (
          <div className="glass-card bg-red-500/10 border-red-500/30 p-4 text-red-400 text-sm font-medium">
            Error: {error}
          </div>
        )}
      </div>

      {/* Right Column: AI orchestration visualization */}
      <div className="lg:w-2/3 flex flex-col gap-6 min-h-[600px]">
        {runId ? (
          <>
            <div className="flex items-center justify-between">
              <div className="text-sm font-mono text-slate-500">Run ID: <span className="text-slate-300">{runId}</span></div>
              <div className="text-sm text-slate-500">
                Iteration: <span className="font-mono text-slate-300">{statusData?.iteration_count || 0}</span>
              </div>
            </div>

            <StatusTracker 
              currentNode={statusData?.current_node || 'inventory'} 
              status={statusData?.status || 'queued'} 
            />

            {statusData?.status === 'awaiting_approval' && statusData?.decision && (
              <ApprovalPanel 
                runId={runId} 
                decision={statusData.decision} 
                onApproval={handleApproval} 
              />
            )}

            <div className="flex-1">
              <AgentLogPanel agentLogs={statusData?.agent_logs || []} />
            </div>

            {/* Business-Friendly Final Decision Panel */}
            <FinalDecisionPanel 
              inventory={statusData?.inventory}
              riskReport={statusData?.risk_report}
              suppliers={statusData?.suppliers}
              decision={statusData?.decision}
              onApproval={handleApproval}
              status={statusData?.status}
              loading={loading}
            />
          </>
        ) : (
          <div className="glass-card flex-1 flex flex-col items-center justify-center p-12 text-center border-dashed border-slate-600/50">
            <div className="w-24 h-24 mb-6 opacity-20 relative">
              <div className="absolute inset-0 border-4 border-dashed border-white rounded-full animate-spin-slow"></div>
              <div className="absolute inset-2 border-4 border-dashed border-brand-500 rounded-full animate-[spin_4s_linear_infinite_reverse]"></div>
            </div>
            <h3 className="text-xl font-semibold text-slate-300 mb-2">System Idle</h3>
            <p className="text-slate-500 max-w-sm">
              Trigger an incident on the left to watch the multi-agent system analyze, reason, and autonomously resolve the supply chain disruption.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
