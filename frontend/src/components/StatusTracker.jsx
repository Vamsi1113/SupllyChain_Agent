import React from 'react';

const NODES = [
  { id: 'inventory', label: 'Inventory Check', icon: '📦' },
  { id: 'risk', label: 'Risk Analysis', icon: '🛡️' },
  { id: 'supplier', label: 'Supplier Search', icon: '🔎' },
  { id: 'validation', label: 'Validation', icon: '✅' },
  { id: 'decision', label: 'Decision Logic', icon: '⚖️' },
  { id: 'approval', label: 'Human Approval', icon: '👤' },
  { id: 'execute', label: 'Execution', icon: '🚀' },
];

export default function StatusTracker({ currentNode, status }) {
  // Determine index of current node
  const currentIndex = NODES.findIndex(n => n.id === currentNode);

  // If failed or human fallback, we color the current node red
  const isErrorState = status === 'failed' || status === 'human_fallback';

  return (
    <div className="glass-card p-6 mb-6 overflow-hidden">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-semibold text-slate-200">Orchestration Graph</h3>
        <span className={`badge ${
          status === 'completed' ? 'badge-success' :
          status === 'awaiting_approval' ? 'badge-warning' :
          isErrorState ? 'badge-danger' :
          'badge-info animate-pulse'
        }`}>
          {status.toUpperCase().replace('_', ' ')}
        </span>
      </div>

      <div className="relative">
        {/* Connecting line background */}
        <div className="absolute top-1/2 left-4 right-4 h-1 bg-surface-600/50 -translate-y-1/2 rounded-full z-0" />
        
        {/* Active connecting line */}
        <div 
          className="absolute top-1/2 left-4 h-1 bg-brand-500 -translate-y-1/2 rounded-full z-0 transition-all duration-500 ease-out"
          style={{ width: `calc(${(Math.max(0, currentIndex) / (NODES.length - 1)) * 100}% - 32px)` }}
        />

        <div className="relative z-10 flex justify-between">
          {NODES.map((node, index) => {
            const isDone = index < currentIndex || status === 'completed';
            const isActive = index === currentIndex && !isDone;
            
            let nodeClass = 'node-pending';
            if (isDone) nodeClass = 'node-done';
            if (isActive) {
              nodeClass = isErrorState ? 'border-red-500 bg-red-500/10 shadow-lg shadow-red-500/20' : 'node-active animate-glow';
            }

            return (
              <div key={node.id} className="flex flex-col items-center gap-2">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${nodeClass}`}>
                  <span className="text-lg">{node.icon}</span>
                </div>
                <div className="text-xs font-medium text-slate-400 max-w-[60px] text-center leading-tight">
                  {node.label}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
