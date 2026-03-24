import React, { useState } from 'react';

const STEP_COLORS = {
  thought: 'text-brand-400',
  action: 'text-purple-400',
  observation: 'text-emerald-400',
};

const STEP_ICONS = {
  thought: '💭',
  action: '⚡',
  observation: '👁️',
};

function ReActStep({ step, index }) {
  const [open, setOpen] = useState(index === 0);
  return (
    <div className="border border-slate-700/40 rounded-xl overflow-hidden mb-2 animate-fade-in">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-3 px-4 py-2.5 bg-surface-700/40 hover:bg-surface-600/40 transition-colors text-left"
      >
        <span className="text-sm">{open ? '▾' : '▸'}</span>
        <div className="flex gap-4 flex-1 text-xs font-mono">
          <span className={STEP_COLORS.thought}>💭 Thought</span>
          <span className={STEP_COLORS.action}>⚡ Action</span>
          <span className={STEP_COLORS.observation}>👁️ Observation</span>
        </div>
        <span className="text-xs text-slate-500">Step {index + 1}</span>
      </button>
      {open && (
        <div className="px-4 py-3 space-y-3 bg-surface-800/30">
          {[
            { key: 'thought', label: 'Thought', value: step.thought },
            { key: 'action', label: 'Action', value: step.action },
            { key: 'observation', label: 'Observation', value: step.observation },
          ].map(({ key, label, value }) => (
            <div key={key}>
              <div className={`text-xs font-semibold uppercase tracking-wider mb-1 ${STEP_COLORS[key]}`}>
                {STEP_ICONS[key]} {label}
              </div>
              <div className="text-xs font-mono text-slate-300 bg-surface-900/60 rounded-lg px-3 py-2 whitespace-pre-wrap break-words">
                {value || '—'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function AgentSection({ log }) {
  const [collapsed, setCollapsed] = useState(false);

  const agentColors = {
    InventoryAgent: 'border-brand-500/50 text-brand-400',
    RiskAgent: 'border-red-500/50 text-red-400',
    SupplierAgent: 'border-purple-500/50 text-purple-400',
    DecisionAgent: 'border-amber-500/50 text-amber-400',
    ValidationAgent: 'border-emerald-500/50 text-emerald-400',
  };
  const colorClass = agentColors[log.agent_name] || 'border-slate-600/50 text-slate-400';

  return (
    <div className={`glass-card border-l-2 ${colorClass.split(' ')[0]} mb-4 overflow-hidden`}>
      <button
        onClick={() => setCollapsed(c => !c)}
        className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-surface-700/20 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className={`font-semibold text-sm ${colorClass.split(' ')[1]}`}>
            {log.agent_name}
          </span>
          {log.error && (
            <span className="badge-danger text-xs">Error</span>
          )}
          {log.duration_ms && (
            <span className="text-xs text-slate-500">{Math.round(log.duration_ms)}ms</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">{log.steps?.length || 0} steps</span>
          <span className="text-xs text-slate-500">{collapsed ? '▸' : '▾'}</span>
        </div>
      </button>

      {!collapsed && (
        <div className="px-5 pb-4">
          {log.error && (
            <div className="mb-3 p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-xs font-mono">
              Error: {log.error}
            </div>
          )}

          {log.steps?.length > 0 && (
            <div>
              <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">ReAct Trace</div>
              {log.steps.map((step, i) => (
                <ReActStep key={i} step={step} index={i} />
              ))}
            </div>
          )}

          {log.output && (
            <div className="mt-3">
              <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">Output</div>
              <pre className="text-xs font-mono text-emerald-300 bg-surface-900/60 rounded-xl px-4 py-3 overflow-x-auto">
                {JSON.stringify(log.output, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function AgentLogPanel({ agentLogs = [] }) {
  if (!agentLogs.length) {
    return (
      <div className="glass-card p-8 text-center animate-fade-in">
        <div className="text-4xl mb-3">🤖</div>
        <div className="text-slate-400 text-sm">Agent logs will appear here once the run starts…</div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Agent Reasoning Trace
        </h3>
        <span className="badge-info">{agentLogs.length} agents</span>
      </div>
      {agentLogs.map((log, i) => (
        <AgentSection key={i} log={log} />
      ))}
    </div>
  );
}
