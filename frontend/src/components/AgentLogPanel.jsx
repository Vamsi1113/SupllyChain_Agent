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
    <div className="mb-3 animate-fade-in group">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-3 md:gap-4 px-4 md:px-5 py-3 md:py-4 bg-surface-lowest hover:bg-surface-low transition-all duration-300 rounded-2xl text-left shadow-inner"
      >
        <span className="text-brand text-xs transition-transform duration-300" style={{ transform: open ? 'rotate(90deg)' : 'none' }}>▶</span>
        <div className="flex gap-4 md:gap-6 flex-1">
          <span className={`${STEP_COLORS.thought} label-text opacity-80`}>Thought</span>
          <span className={`${STEP_COLORS.action} lg:inline-block label-text opacity-80 hidden`}>Action</span>
          <span className={`${STEP_COLORS.observation} lg:inline-block label-text opacity-80 hidden`}>Obs</span>
        </div>
        <div className="label-text opacity-40">Step {index + 1}</div>
      </button>
      {open && (
        <div className="mt-2 px-6 py-5 space-y-5 bg-surface-low rounded-2xl border-t border-white/5 animate-slide-up">
          {[
            { key: 'thought', label: 'Internal Reasoning', value: step.thought },
            { key: 'action', label: 'Tool Invocation', value: step.action },
            { key: 'observation', label: 'System Response', value: step.observation },
          ].map(({ key, label, value }) => (
            <div key={key} className="relative pl-6">
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-surface-highest rounded-full overflow-hidden">
                <div className={`h-full w-full ${STEP_COLORS[key].replace('text-', 'bg-')} opacity-60`}></div>
              </div>
              <div className={`label-text mb-2 ${STEP_COLORS[key]}`}>
                {label}
              </div>
              <div className="text-xs font-mono text-slate-300 leading-relaxed whitespace-pre-wrap">
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
    InventoryAgent: 'brand',
    RiskAgent: 'accent-red',
    SupplierAgent: 'purple-500',
    DecisionAgent: 'amber-500',
    ValidationAgent: 'emerald-500',
  };
  const colorKey = agentColors[log.agent_name] || 'slate-500';

  return (
    <div className="orchestration-beam mb-10 group">
      <div className="stitch-card overflow-hidden">
        <button
          onClick={() => setCollapsed(c => !c)}
          className="w-full flex items-center justify-between px-6 md:px-8 py-5 md:py-6 hover:bg-white/5 transition-all duration-500"
        >
          <div className="flex items-center gap-4 md:gap-6">
            <div className={`w-3 h-3 rounded-full bg-${colorKey} shadow-lg shadow-${colorKey}/40 animate-pulse`}></div>
            <span className="text-base md:text-lg font-bold text-white tracking-tight">
              {log.agent_name}
            </span>
            {log.error && (
              <span className="badge-stitch text-red-400 bg-red-400/5 px-2 md:px-3 py-1">Failure</span>
            )}
          </div>
          <div className="flex items-center gap-4 md:gap-6">
            <div className="text-right hidden sm:block">
              <div className="label-text opacity-40">Performance</div>
              <div className="text-xs font-mono text-slate-400">{Math.round(log.duration_ms || 0)}ms</div>
            </div>
            <span className="text-slate-500 transition-transform duration-500" style={{ transform: collapsed ? 'none' : 'rotate(180deg)' }}>▾</span>
          </div>
        </button>

        {!collapsed && (
          <div className="px-8 pb-8 animate-slide-up">
            {log.error && (
              <div className="mb-6 p-5 bg-red-400/5 border border-red-400/10 rounded-2xl text-red-400 text-xs font-mono leading-relaxed">
                {log.error}
              </div>
            )}

            {log.steps?.length > 0 && (
              <div className="mt-2">
                <div className="label-text mb-6 opacity-40">Reasoning Trajectory</div>
                <div className="space-y-4">
                  {log.steps.map((step, i) => (
                    <ReActStep key={i} step={step} index={i} />
                  ))}
                </div>
              </div>
            )}

            {log.output && (
              <div className="mt-8">
                <div className="label-text mb-4 opacity-40">Agent Consensus</div>
                <pre className="text-xs font-mono text-emerald-400 bg-surface-lowest rounded-2xl px-6 py-5 overflow-x-auto shadow-inner border border-white/5">
                  {JSON.stringify(log.output, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function AgentLogPanel({ agentLogs = [] }) {
  if (!agentLogs.length) {
    return (
      <div className="stitch-card p-20 text-center animate-fade-in group">
        <div className="w-20 h-20 bg-surface-low rounded-full mx-auto mb-8 flex items-center justify-center text-4xl opacity-20 group-hover:opacity-40 transition-opacity">
          🤖
        </div>
        <div className="label-text opacity-40 tracking-[0.2em]">Monitoring Neutral Status</div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <div className="flex items-end justify-between mb-8 px-2">
        <div>
          <h3 className="text-2xl font-bold text-white tracking-tighter uppercase">
            Intel Stream
          </h3>
          <div className="label-text mt-1 opacity-50">Cross-Agent Neural Logs</div>
        </div>
        <div className="badge-stitch border border-white/5 px-4 py-2">
          {agentLogs.length} Synchronized Nodes
        </div>
      </div>
      <div className="mt-8">
        {agentLogs.map((log, i) => (
          <AgentSection key={i} log={log} />
        ))}
      </div>
    </div>
  );
}
