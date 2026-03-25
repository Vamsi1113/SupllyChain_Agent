import React, { useState } from 'react';
import { submitApproval } from '../services/api';

export default function ApprovalPanel({ runId, decision, onApproval }) {
  const [loading, setLoading] = useState(false);
  const [comments, setComments] = useState('');
  const [done, setDone] = useState(false);
  const [approved, setApproved] = useState(null);

  const supplier = decision?.recommended_supplier || {};
  const totalCost = decision?.estimated_total_cost || 0;

  async function handleDecision(isApproved) {
    setLoading(true);
    try {
      // Logic moved to Parent Dashboard for state sync
      await onApproval?.(isApproved, comments);
      setApproved(isApproved);
      setDone(true);
    } catch (err) {
      alert(`Approval failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  if (done) {
    return (
      <div className={`stitch-card p-10 mt-10 animate-fade-in text-center ${approved ? 'bg-emerald-400/5' : 'bg-red-400/5'}`}>
        <div className="flex flex-col items-center gap-6">
          <div className={`w-20 h-20 rounded-full flex items-center justify-center text-4xl shadow-2xl ${approved ? 'bg-emerald-400/20 text-emerald-400' : 'bg-red-400/20 text-red-400'}`}>
            {approved ? '✓' : '✕'}
          </div>
          <div>
            <h3 className={`text-2xl font-bold tracking-tighter ${approved ? 'text-emerald-400' : 'text-red-400'}`}>
              {approved ? 'Decision Authorized' : 'Authorization Denied'}
            </h3>
            <div className="label-text mt-2 opacity-60">Neural weights updated. Resuming orchestration.</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="stitch-card-high p-6 md:p-10 mt-6 md:mt-10 relative overflow-hidden group">
      {/* Background Spectral Glow */}
      <div className="absolute -top-24 -right-24 w-64 h-64 bg-brand/10 rounded-full blur-[100px] pointer-events-none"></div>
      
      {/* Header */}
      <div className="flex items-center gap-4 md:gap-6 mb-8 md:mb-10">
        <div className="w-12 h-12 md:w-14 md:h-14 rounded-2xl bg-brand/10 flex items-center justify-center text-xl md:text-2xl shadow-inner border border-white/5">
          👤
        </div>
        <div>
          <h3 className="text-xl md:text-2xl font-bold text-white tracking-tight">Executive Authorization</h3>
          <div className="label-text mt-1 opacity-50">Human-in-the-loop Protocol {runId?.slice(0, 8)}</div>
        </div>
      </div>

      {/* Decision Summary */}
      {decision && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          <InfoTile icon="🏭" label="Procurement Path" value={supplier.supplier_name || '—'} />
          <InfoTile icon="💰" label="CapEx Impact" value={`$${totalCost.toLocaleString('en-US', { minimumFractionDigits: 2 })}`} />
          <InfoTile icon="📦" label="Unit Volume" value={`${decision.quantity_to_order?.toLocaleString()} Items`} />
          <InfoTile icon="⏱️" label="SLA Buffer" value={`${supplier.lead_time_days} Days`} />
          <InfoTile icon="📍" label="Origin Node" value={supplier.location || '—'} />
          <InfoTile icon="⭐" label="AI Confidence" value={`${(decision.composite_score * 10).toFixed(1)}%`} />
        </div>
      )}

      {/* Reason */}
      {decision?.reason && (
        <div className="mb-8 p-6 bg-surface-lowest rounded-2xl border border-white/5 shadow-inner">
          <div className="label-text mb-3 opacity-40">AI Strategic Rationalization</div>
          <p className="text-sm text-slate-300 leading-relaxed italic">"{decision.reason}"</p>
        </div>
      )}

      {/* Comments */}
      <div className="mb-10">
        <label className="label-text block mb-3 opacity-60 px-1">Reviewer Annotations (Optional)</label>
        <textarea
          className="input-stitch resize-none h-28 text-sm placeholder:opacity-30"
          placeholder="Document the rationale for this override or approval..."
          value={comments}
          onChange={e => setComments(e.target.value)}
        />
      </div>

      {/* Buttons */}
      <div className="flex flex-col sm:flex-row gap-4 md:gap-6">
        <button
          id="approve-btn"
          className="btn-gradient flex-1 flex items-center justify-center gap-3 py-4 text-base md:text-lg"
          onClick={() => handleDecision(true)}
          disabled={loading}
        >
          {loading ? (
            <div className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
          ) : (
            <><span>✓</span> <span>Authorize Plan</span></>
          )}
        </button>
        <button
          id="reject-btn"
          className="btn-secondary flex-1 flex items-center justify-center gap-3 py-4 text-base md:text-lg hover:bg-accent-red/10 hover:text-accent-red transition-all"
          onClick={() => handleDecision(false)}
          disabled={loading}
        >
          {loading ? (
            <div className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
          ) : (
            <><span>✕</span> <span>Reject & Redirect</span></>
          )}
        </button>
      </div>
    </div>
  );
}

function InfoTile({ icon, label, value }) {
  return (
    <div className="bg-surface-low rounded-2xl p-5 border border-white/5 hover:bg-surface-container transition-colors duration-300 shadow-sm">
      <div className="label-text opacity-40 mb-2 whitespace-nowrap overflow-hidden text-ellipsis">
        {icon} {label}
      </div>
      <div className="text-lg font-bold text-white tracking-tight truncate">{value}</div>
    </div>
  );
}
