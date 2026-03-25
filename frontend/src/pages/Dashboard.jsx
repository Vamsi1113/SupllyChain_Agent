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
    <div className="min-h-screen p-4 md:p-8 lg:p-12 max-w-[1600px] mx-auto flex flex-col lg:flex-row gap-8 lg:gap-12 antialiased overflow-x-hidden">
      
      {/* Left Column: The Control Deck (Form & Key Info) */}
      <div className="w-full lg:w-[350px] flex flex-col gap-6 md:gap-8 shrink-0">
        <header className="mb-4">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-brand to-brand-dark rounded-2xl flex items-center justify-center shadow-2xl shadow-brand/40">
              <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tighter text-white leading-none">
                SC Orchestrator
              </h1>
              <div className="label-text mt-1">Autonomous Intelligence</div>
            </div>
          </div>
          <p className="text-slate-500 text-sm leading-relaxed pr-4">
            Managing global disruption through real-time kinetic orchestration.
          </p>
        </header>

        <div className="stitch-card p-6 shadow-2xl">
          <IncidentCard onSubmit={handleIncidentSubmit} loading={loading} />
        </div>

        {error && (
          <div className="stitch-card-high bg-red-500/5 border border-red-500/20 p-4 text-red-400 text-sm font-medium animate-slide-up">
            <span className="font-bold mr-2 uppercase text-[10px] tracking-widest">Error Trace</span>
            {error}
          </div>
        )}
      </div>

      {/* Right Column: The Global View (AI orchestration visualization) */}
      <div className="flex-1 flex flex-col gap-10">
        {runId ? (
          <>
            <div className="flex items-end justify-between px-2">
              <div>
                <div className="label-text mb-1">Active Run Context</div>
                <div className="text-xs font-mono text-slate-400 opacity-60">ID: {runId}</div>
              </div>
              <div className="text-right">
                <div className="label-text mb-1">Cycle Count</div>
                <div className="text-xl font-bold text-white tracking-tighter">{statusData?.iteration_count || 1}</div>
              </div>
            </div>

            <div className="stitch-card-low p-8">
              <StatusTracker 
                currentNode={statusData?.current_node || 'inventory'} 
                status={statusData?.status || 'queued'} 
              />
            </div>

            {statusData?.status === 'awaiting_approval' && statusData?.decision && (
              <div className="animate-slide-up">
                <ApprovalPanel 
                  runId={runId} 
                  decision={statusData.decision} 
                  onApproval={handleApproval} 
                />
              </div>
            )}

            <div className="flex flex-col gap-12">
              <div className="flex-1">
                <AgentLogPanel agentLogs={statusData?.agent_logs || []} />
              </div>

              {/* Business-Friendly Final Decision Panel */}
              <div className="animate-slide-up">
                <FinalDecisionPanel 
                  inventory={statusData?.inventory}
                  riskReport={statusData?.risk_report}
                  suppliers={statusData?.suppliers}
                  decision={statusData?.decision}
                  onApproval={handleApproval}
                  status={statusData?.status}
                  loading={loading}
                />
              </div>
            </div>
          </>
        ) : (
          <div className="stitch-card flex-1 flex flex-col items-center justify-center p-20 text-center relative overflow-hidden group">
            {/* Background Atmosphere */}
            <div className="absolute inset-0 bg-gradient-to-b from-brand/5 to-transparent opacity-50"></div>
            
            <div className="relative z-10">
              <div className="w-32 h-32 mb-10 mx-auto relative group-hover:scale-105 transition-transform duration-700">
                <div className="absolute inset-0 border-[3px] border-dashed border-white/5 rounded-full animate-spin-slow"></div>
                <div className="absolute inset-4 border-[3px] border-dashed border-brand/20 rounded-full animate-[spin_6s_linear_infinite_reverse]"></div>
                <div className="absolute inset-0 flex items-center justify-center text-5xl opacity-40">🛰️</div>
              </div>
              
              <h3 className="display-text mb-4">System At Rest</h3>
              <p className="text-slate-500 max-w-md mx-auto leading-relaxed">
                Initiate a disruption query on the control deck to activate the orchestration engine.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
