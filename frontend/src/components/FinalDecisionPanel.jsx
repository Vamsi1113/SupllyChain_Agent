import React, { useState } from 'react';

/**
 * FinalDecisionPanel
 * Transforms technical agent outputs into a business-friendly response UI.
 */
export default function FinalDecisionPanel({ inventory, riskReport, suppliers, decision, onApproval, loading }) {
  const [selectedSupplierId, setSelectedSupplierId] = useState(decision?.recommended_supplier?.supplier_id || '');
  const [showScoring, setShowScoring] = useState(false);

  // If no data yet, show a clean loading skeleton or idle state
  if (!inventory && !loading) return null;

  if (loading && !inventory) {
    return (
      <div className="glass-card p-6 animate-pulse border border-slate-700/50">
        <div className="h-4 bg-slate-700 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          <div className="h-8 bg-slate-800 rounded"></div>
          <div className="h-24 bg-slate-800 rounded"></div>
        </div>
      </div>
    );
  }

  // --- Helpers ---
  const formatCurrency = (val) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
  
  const getSeverityColor = (sev) => {
    const s = sev?.toLowerCase();
    if (s === 'critical' || s === 'high') return 'text-red-400 bg-red-400/10 border-red-500/20';
    if (s === 'medium') return 'text-amber-400 bg-amber-400/10 border-amber-500/20';
    return 'text-emerald-400 bg-emerald-400/10 border-emerald-500/20';
  };

  const selectedSupplier = suppliers?.find(s => s.supplier_id === selectedSupplierId) || decision?.recommended_supplier;

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      <div className="flex items-center gap-2 mb-2">
        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-slate-700 to-transparent"></div>
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">Final AI Decision Output</span>
        <div className="h-px flex-1 bg-gradient-to-r from-slate-700 via-slate-700 to-transparent"></div>
      </div>

      {/* 1. 🧾 Incident Summary (Top Card) */}
      <div className="glass-card border-brand-500/30 p-5 relative overflow-hidden group">
        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
          <span className="text-6xl">🧾</span>
        </div>
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Incident Summary</h3>
        <p className="text-lg text-slate-100 leading-relaxed max-w-2xl">
          <span className="font-bold text-brand-400">{inventory?.part_id || 'Part'}</span> is facing a 
          <span className="font-semibold text-white"> {riskReport?.query || 'disruption'}</span>. 
          Current stock is <span className="font-bold text-white">{inventory?.current_stock || 0} units</span>, 
          but <span className="font-bold text-white">{inventory?.reorder_threshold || 0} units</span> are required. 
          Risk severity is <span className={`px-2 py-0.5 rounded border text-sm font-bold ml-1 ${getSeverityColor(riskReport?.severity)}`}>
            {riskReport?.severity?.toUpperCase() || 'UNKNOWN'}
          </span>.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 2. 📦 Inventory Insight */}
        <div className="glass-card p-5 border-slate-700/50">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xl">📦</span>
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Inventory Insight</h3>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed">
            You currently have <span className="text-white font-semibold">{inventory?.current_stock} units</span> in stock at <span className="text-slate-400 italic">{inventory?.location}</span>, which is below the required threshold of <span className="text-white font-semibold">{inventory?.reorder_threshold} units</span>. 
            There is a critical deficit of <span className="text-red-400 font-bold">{(inventory?.reorder_threshold - inventory?.current_stock) || 0} units</span>.
          </p>
        </div>

        {/* 3. 🌍 Risk Insight */}
        <div className="glass-card p-5 border-slate-700/50">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xl">🌍</span>
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Risk Insight</h3>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed">
            This disruption is classified as <span className="text-amber-400 font-semibold">{riskReport?.severity?.toUpperCase() || 'MODERATE'}</span> severity 
            {riskReport?.estimated_duration_days ? ` and is expected to last approximately ${riskReport.estimated_duration_days} days.` : '.'}
            {riskReport?.summary && <span className="block mt-2 text-slate-400 text-xs italic">{riskReport.summary}</span>}
          </p>
        </div>
      </div>

      {/* 4. 🏭 Supplier Options (Dropdown List) */}
      <div className="glass-card p-6 border-slate-700/50">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-2">
            <span className="text-xl">🏭</span>
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Alternative Suppliers Found</h3>
          </div>
          <select 
            value={selectedSupplierId}
            onChange={(e) => setSelectedSupplierId(e.target.value)}
            className="input-field py-1 text-sm min-w-[240px]"
          >
            <option value="">Select a supplier to view details</option>
            {suppliers?.map(sup => (
              <option key={sup.supplier_id} value={sup.supplier_id}>
                {sup.supplier_name} — {formatCurrency(sup.unit_price)} ({sup.lead_time_days}d)
              </option>
            ))}
          </select>
        </div>

        {selectedSupplier && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-slide-up">
            <DetailTile label="Unit Price" value={formatCurrency(selectedSupplier.unit_price)} />
            <DetailTile label="Lead Time" value={`${selectedSupplier.lead_time_days} Days`} />
            <DetailTile label="Reliability" value={`${(selectedSupplier.reliability_score * 100).toFixed(0)}%`} />
            <DetailTile label="Location" value={selectedSupplier.location} />
          </div>
        )}
      </div>

      {/* 5. 🧠 AI Recommendation (Highlight Card) */}
      <div className="glass-card border-brand-500 bg-brand-500/5 p-8 relative overflow-hidden shadow-2xl shadow-brand-500/10">
        <div className="absolute top-0 right-0 p-6 opacity-20 pointer-events-none">
          <span className="text-8xl">🧠</span>
        </div>
        
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500 text-white text-[10px] font-bold uppercase tracking-widest mb-4">
            AI Recommendation
          </div>
          
          <h2 className="text-3xl font-bold text-white mb-4">
            Procure from <span className="text-brand-400">{decision?.recommended_supplier?.supplier_name}</span>
          </h2>
          
          <p className="text-lg text-slate-300 max-w-3xl mb-8 leading-relaxed">
            {decision?.reason || "Based on trade-off analysis, we recommend this supplier to minimize disruption and cost."}
          </p>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <Stat label="Estimated Total Cost" value={formatCurrency(decision?.estimated_total_cost)} highlight />
            <Stat label="Total Quantity" value={`${decision?.quantity_to_order?.toLocaleString()} Units`} />
            <Stat label="Delivery Timeline" value={`${decision?.recommended_supplier?.lead_time_days} Business Days`} />
            <Stat label="Overall Confidence" value={`${(decision?.composite_score * 10 || 85).toFixed(0)}%`} />
          </div>
        </div>
      </div>

      {/* 6. ⚖️ Decision Breakdown (Expandable) */}
      <div className="glass-card border-slate-700/50 overflow-hidden text-sm">
        <button 
          onClick={() => setShowScoring(!showScoring)}
          className="w-full flex items-center justify-between px-6 py-4 hover:bg-surface-700/30 transition-colors"
        >
          <div className="flex items-center gap-2">
            <span className="text-xl">⚖️</span>
            <h3 className="font-bold text-slate-400 uppercase tracking-widest text-xs">AI Scoring Breakdown</h3>
          </div>
          <span className="text-slate-500">{showScoring ? 'Close' : 'View Scores'}</span>
        </button>
        
        {showScoring && (
          <div className="px-6 pb-6 pt-2 animate-slide-up">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 content-center text-center">
              <Score label="Cost Score" value={decision?.cost_score} color="text-emerald-400" />
              <Score label="ETA Score" value={decision?.eta_score} color="text-brand-400" />
              <Score label="Risk Score" value={decision?.risk_score} color="text-red-400" />
              <Score label="Composite" value={decision?.composite_score} color="text-white font-bold" />
            </div>
            <div className="mt-6 text-[10px] text-slate-500 italic text-center uppercase tracking-wider">
              Scores are weighted by priority: Cost (30%), Speed (40%), Risk (30%)
            </div>
          </div>
        )}
      </div>

      {/* 7. 🚀 Action Panel - Only show when awaiting approval */}
      {status === 'awaiting_approval' && (
        <div className="flex gap-4 pt-4 sticky bottom-6 z-20 animate-slide-up">
          <button 
            onClick={() => onApproval?.(true)}
            className="flex-1 btn-success py-4 text-lg shadow-xl shadow-emerald-500/20 flex items-center justify-center gap-3 transition-transform hover:scale-[1.02] active:scale-[0.98]"
          >
            <span className="text-xl">✅</span> Approve Procurement Action
          </button>
          <button 
            onClick={() => onApproval?.(false)}
            className="flex-none btn-danger px-8 py-4 opacity-80 hover:opacity-100 transition-all"
          >
            <span className="text-xl">❌</span> Reject
          </button>
        </div>
      )}

      {status === 'completed' && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-center font-bold animate-fade-in">
          ✅ Procurement Action Successfully Executed
        </div>
      )}
    </div>
  );
}

function DetailTile({ label, value }) {
  return (
    <div className="p-3 bg-surface-900/40 rounded-xl border border-slate-800/50">
      <div className="text-[10px] text-slate-500 uppercase tracking-widest font-bold mb-1">{label}</div>
      <div className="text-sm font-semibold text-slate-200">{value}</div>
    </div>
  );
}

function Stat({ label, value, highlight }) {
  return (
    <div className="flex flex-col">
      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">{label}</span>
      <span className={`text-xl font-bold ${highlight ? 'text-brand-400' : 'text-white'}`}>{value || '—'}</span>
    </div>
  );
}

function Score({ label, value, color }) {
  return (
    <div className="flex flex-col items-center">
      <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">{label}</div>
      <div className={`text-2xl ${color}`}>{value?.toFixed(1) || '0.0'}</div>
    </div>
  );
}
