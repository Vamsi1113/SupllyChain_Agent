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
    <div className="w-full">
      <div className="flex items-center justify-between mb-10 px-2">
        <div>
          <h3 className="text-xl font-bold text-white tracking-tight">Orchestration Graph</h3>
          <div className="label-text mt-1 opacity-50">Real-time Node Status</div>
        </div>
        <div className={`badge-stitch px-4 py-2 border border-white/5 ${
          status === 'completed' ? 'text-emerald-400 bg-emerald-400/5' :
          status === 'awaiting_approval' ? 'text-amber-400 bg-amber-400/5' :
          isErrorState ? 'text-red-400 bg-red-400/5' :
          'text-brand bg-brand/5'
        }`}>
          {status.toUpperCase().replace('_', ' ')}
        </div>
      </div>

      <div className="relative px-4 overflow-x-auto custom-scrollbar-hide pb-4">
        {/* The Orchestration Beam - Background */}
        <div className="absolute top-6 left-10 right-10 h-[2px] bg-white/5 z-0 min-w-[600px] md:min-w-0" />
        
        {/* The Orchestration Beam - Active Gradient */}
        <div 
          className="absolute top-6 left-10 h-[2px] z-0 transition-all duration-1000 ease-in-out min-w-[600px] md:min-w-0"
          style={{ 
            width: `calc(${(Math.max(0, currentIndex) / (NODES.length - 1)) * 100}% - 4px)`,
            background: 'linear-gradient(90deg, #6366f1 0%, #c0c1ff 100%)',
            boxShadow: '0 0 15px rgba(99, 102, 241, 0.5)'
          }}
        />

        <div className="relative z-10 flex justify-between min-w-[600px] md:min-w-0 gap-4">
          {NODES.map((node, index) => {
            const isDone = index < currentIndex || status === 'completed';
            const isActive = index === currentIndex && !isDone;
            
            let stateClass = "bg-surface-lowest text-slate-500 opacity-40 shadow-inner";
            if (isDone) stateClass = "bg-brand text-white shadow-lg shadow-brand/20";
            if (isActive) {
              stateClass = isErrorState 
                ? "bg-accent-red text-white shadow-lg shadow-accent-red/40 animate-pulse" 
                : "bg-white text-surface-900 shadow-2xl shadow-white/20 scale-110 border-4 border-brand";
            }

            return (
              <div key={node.id} className="flex flex-col items-center group shrink-0 w-20 md:w-auto">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-500 ${stateClass}`}>
                  <span className="text-xl">{node.icon}</span>
                </div>
                <div className={`label-text mt-4 transition-colors duration-300 text-center ${isActive ? 'text-white' : 'text-slate-500'}`}>
                  {node.label.split(' ')[0]}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
