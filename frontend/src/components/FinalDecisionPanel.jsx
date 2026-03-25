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
      <div className="stitch-card p-10 animate-pulse">
        <div className="h-4 bg-surface-highest rounded-full w-32 mb-8"></div>
        <div className="space-y-6">
          <div className="h-12 bg-surface-highest rounded-2xl w-3/4"></div>
          <div className="h-32 bg-surface-highest rounded-2xl"></div>
        </div>
      </div>
    );
  }

  // --- Helpers ---
  const formatCurrency = (val) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
  
  const getSeverityColor = (sev) => {
    const s = sev?.toLowerCase();
    if (s === 'critical' || s === 'high') return 'text-red-400 bg-red-400/10';
    if (s === 'medium') return 'text-tertiary bg-tertiary/10';
    return 'text-emerald-400 bg-emerald-400/10';
  };

  const selectedSupplier = suppliers?.find(s => s.supplier_id === selectedSupplierId) || decision?.recommended_supplier;

  return (
    <div className="space-y-12 animate-fade-in pb-20">
      
      {/* 1. 🧾 Incident Summary (Main Context Card) */}
      <div className="stitch-card-high p-6 md:p-10 relative overflow-hidden group">
        <div className="absolute -right-20 -top-20 w-80 h-80 bg-brand/5 rounded-full blur-[80px] group-hover:bg-brand/10 transition-colors duration-700"></div>
        
        <header className="relative z-10 mb-8">
          <div className="label-text opacity-50 mb-4">Strategic Incident Briefing</div>
          <h2 className="text-3xl md:text-5xl font-semibold tracking-tighter text-white leading-tight">
            Critical disruption identified for <span className="text-brand">{inventory?.part_id || 'Part'}</span>
          </h2>
        </header>
        <div className="relative z-10 flex flex-col md:flex-row gap-8 items-start md:items-center">
          <p className="flex-1 text-lg md:text-xl text-slate-300 leading-relaxed font-medium">
            A <span className="text-white italic">{riskReport?.query || 'disruption event'}</span> has breached the reorder threshold. 
            Operational continuity requires <span className="text-white font-bold">{inventory?.reorder_threshold || 0} units</span>, 
            representing a deficit of <span className="text-brand font-bold">{(inventory?.reorder_threshold - inventory?.current_stock) || 0}</span> from the current <span className="text-slate-400">{inventory?.current_stock || 0}</span> items.
          </p>
          <div className={`px-6 py-3 rounded-2xl label-text border border-white/5 shadow-inner shrink-0 ${getSeverityColor(riskReport?.severity)}`}>
            {riskReport?.severity || 'Assessing...'} Severity
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 2. 📦 Inventory Insight */}
        <div className="stitch-card p-8 group hover:bg-surface-high transition-all duration-500">
          <div className="label-text opacity-40 mb-6 flex items-center gap-3">
            <span className="w-2 h-2 rounded-full bg-brand"></span> Node Inventory
          </div>
          <div className="space-y-4">
            <div className="text-slate-400 text-sm leading-relaxed">
              Active stock at <span className="text-white font-semibold">{inventory?.location}</span> is currently at <span className="text-white font-bold">{inventory?.current_stock} units</span>. Reorder triggers are active due to the <span className="text-brand font-bold">{(inventory?.reorder_threshold - inventory?.current_stock) || 0} unit</span> gap.
            </div>
          </div>
        </div>

        {/* 3. 🌍 Risk Insight */}
        <div className="stitch-card p-8 group hover:bg-surface-high transition-all duration-500">
          <div className="label-text opacity-40 mb-6 flex items-center gap-3">
            <span className="w-2 h-2 rounded-full bg-tertiary"></span> Risk Projection
          </div>
          <div className="space-y-4">
            <div className="text-slate-400 text-sm leading-relaxed">
              The environmental impact is rated <span className="text-tertiary font-bold uppercase tracking-widest">{riskReport?.severity || 'Standard'}</span>.
              {riskReport?.estimated_duration_days && ` Active duration projected at ${riskReport.estimated_duration_days} cycle days.`}
              {riskReport?.summary && <div className="mt-4 pt-4 border-t border-white/5 italic text-slate-500 text-xs">AI Note: {riskReport.summary}</div>}
            </div>
          </div>
        </div>
      </div>

      {/* 4. 🏭 Alternative Options Flow */}
      <div className="stitch-card p-10">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-12">
          <div>
            <div className="label-text opacity-40 mb-4">Market Discovery</div>
            <h3 className="text-2xl font-bold text-white tracking-tight">Supply Node Options</h3>
          </div>
          <div className="w-full md:w-[320px]">
            <div className="label-text mb-3 opacity-40 text-right">Switch Active Context</div>
            <select 
              value={selectedSupplierId}
              onChange={(e) => setSelectedSupplierId(e.target.value)}
              className="input-stitch py-3 text-sm bg-surface-lowest text-brand font-semibold"
            >
              <option value="">View Discovered Suppliers...</option>
              {suppliers?.map(sup => (
                <option key={sup.supplier_id} value={sup.supplier_id}>
                  {sup.supplier_name} — {formatCurrency(sup.unit_price)}
                </option>
              ))}
            </select>
          </div>
        </div>

        {selectedSupplier ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 animate-slide-up">
            <DetailTile label="Unit Rate" value={formatCurrency(selectedSupplier.unit_price)} />
            <DetailTile label="Lead Cycles" value={`${selectedSupplier.lead_time_days} Days`} />
            <DetailTile label="Node Reliability" value={`${(selectedSupplier.reliability_score * 100).toFixed(0)}%`} />
            <DetailTile label="Geographic Node" value={selectedSupplier.location} />
          </div>
        ) : (
          <div className="p-12 text-center bg-surface-lowest rounded-3xl opacity-20 border border-dashed border-white/10">
            <div className="label-text uppercase tracking-[0.3em]">No Node Selected</div>
          </div>
        )}
      </div>

      {/* 5. 🧠 The "Hero" Recommendation (Spectral Reveal) */}
      <div className="stitch-card-high p-6 md:p-12 bg-surface-low relative overflow-hidden shadow-[0_40px_100px_-20px_rgba(99,102,241,0.15)]">
        {/* Spectral Glows */}
        <div className="absolute -top-40 -left-40 w-[400px] h-[400px] bg-brand/20 rounded-full blur-[120px] pointer-events-none animate-pulse-slow"></div>
        <div className="absolute -bottom-40 -right-40 w-[400px] h-[400px] bg-brand-container/10 rounded-full blur-[120px] pointer-events-none"></div>

        <div className="relative z-10">
          <div className="inline-flex items-center gap-3 px-5 py-2 rounded-2xl bg-brand text-surface-900 text-[10px] font-black uppercase tracking-[0.2em] mb-8 md:mb-10 shadow-lg shadow-brand/20">
            Orchestration Directives
          </div>
          
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-6 md:mb-8 tracking-tighter max-w-4xl leading-[1.1]">
            AI Strategic Path: <span className="text-brand">Procure from {decision?.recommended_supplier?.supplier_name}</span>
          </h2>
          
          <p className="text-lg md:text-2xl text-slate-400 font-medium max-w-4xl mb-8 md:mb-12 leading-relaxed">
            {decision?.reason || "Autonomous weighting favor this node for optimal reliability/cost synchronization."}
          </p>
          
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 md:gap-10 p-5 md:p-8 bg-surface-lowest/50 backdrop-blur-xl rounded-2xl md:rounded-[2.5rem] border border-white/5 shadow-inner">
            <Stat label="Est. CapEx" value={formatCurrency(decision?.estimated_total_cost)} highlight />
            <Stat label="Total Allocation" value={`${decision?.quantity_to_order?.toLocaleString()} Units`} />
            <Stat label="Node SLA" value={`${decision?.recommended_supplier?.lead_time_days} Days`} />
            <Stat label="Confidence" value={`${((decision?.composite_score || 0.85) * 10).toFixed(1)}%`} />
          </div>
        </div>
      </div>

      {/* 6. ⚖️ Decision Breakdown (Tonal Detail) */}
      <div className="stitch-card overflow-hidden">
        <button 
          onClick={() => setShowScoring(!showScoring)}
          className="w-full flex items-center justify-between px-10 py-6 hover:bg-white/5 transition-all duration-500"
        >
          <div className="flex items-center gap-4">
            <div className="w-8 h-8 rounded-full bg-surface-low flex items-center justify-center text-sm shadow-inner overflow-hidden">
              <div className="w-full h-full bg-gradient-to-tr from-brand/20 to-transparent"></div>
            </div>
            <h3 className="label-text font-bold opacity-50 tracking-[0.2em]">Neural Weights Correlation</h3>
          </div>
          <div className="label-text opacity-40 text-[10px]">{showScoring ? 'Hide Matrix' : 'Expose Logic'}</div>
        </button>
        
        {showScoring && (
          <div className="px-6 md:px-10 pb-10 pt-4 animate-slide-up">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 md:gap-12 text-center py-6 bg-surface-lowest/30 rounded-3xl">
              <Score label="Cost Efficiency" value={decision?.cost_score} color="text-emerald-400" />
              <Score label="Temporal Speed" value={decision?.eta_score} color="text-brand" />
              <Score label="Resilience Risk" value={decision?.risk_score} color="text-accent-red" />
              <Score label="Final Aggregate" value={decision?.composite_score} color="text-white scale-110 md:scale-125 font-black" />
            </div>
            <p className="mt-8 label-text text-center opacity-30 text-[9px] max-w-md mx-auto leading-relaxed">
              Weighted algorithm optimization: Speed (40%), Cost (30%), Resilience (30%). Recalculated dynamically against Tavily market data.
            </p>
          </div>
        )}
      </div>

      {/* 7. Final Action Context */}
      {status === 'completed' && (
        <div className="stitch-card p-8 bg-emerald-400/5 animate-fade-in border border-emerald-400/10">
          <div className="flex items-center gap-6">
            <div className="w-12 h-12 rounded-full bg-emerald-400/20 text-emerald-400 flex items-center justify-center text-xl">✓</div>
            <div>
              <div className="text-xl font-bold text-white tracking-tight">Directive Successfully Synchronized</div>
              <div className="label-text opacity-60 mt-1">Procurement flow active and logged in the ERP node.</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function DetailTile({ label, value }) {
  return (
    <div className="p-6 bg-surface-low rounded-3xl shadow-sm hover:translate-y-[-2px] transition-transform duration-300 group">
      <div className="label-text opacity-30 mb-3 group-hover:opacity-50 transition-opacity whitespace-nowrap overflow-hidden text-ellipsis">{label}</div>
      <div className="text-lg font-bold text-white tracking-tight truncate">{value}</div>
    </div>
  );
}

function Stat({ label, value, highlight }) {
  return (
    <div className="flex flex-col group">
      <span className="label-text opacity-30 mb-2 group-hover:opacity-50 transition-opacity">{label}</span>
      <span className={`text-2xl font-black tracking-tighter ${highlight ? 'text-brand' : 'text-white'}`}>{value || '—'}</span>
    </div>
  );
}

function Score({ label, value, color }) {
  return (
    <div className="flex flex-col items-center group">
      <div className="label-text opacity-30 mb-4 group-hover:opacity-50 transition-opacity">{label}</div>
      <div className={`text-3xl transition-transform duration-500 group-hover:scale-110 ${color}`}>{value?.toFixed(1) || '0.0'}</div>
    </div>
  );
}
