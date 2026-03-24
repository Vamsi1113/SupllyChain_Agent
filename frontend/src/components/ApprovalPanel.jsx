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
      <div className={`glass-card p-6 border animate-fade-in ${approved ? 'border-emerald-500/40' : 'border-red-500/40'}`}>
        <div className="flex items-center gap-3">
          <span className="text-3xl">{approved ? '✅' : '❌'}</span>
          <div>
            <div className={`font-semibold ${approved ? 'text-emerald-400' : 'text-red-400'}`}>
              {approved ? 'Action Approved' : 'Action Rejected'}
            </div>
            <div className="text-sm text-slate-400">Agent is resuming execution…</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card border border-amber-500/30 p-6 animate-slide-up shadow-lg shadow-amber-500/10">
      {/* Header */}
      <div className="flex items-center gap-3 mb-5">
        <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-xl">
          ⚠️
        </div>
        <div>
          <h3 className="font-bold text-amber-400 text-base">Human Approval Required</h3>
          <p className="text-xs text-slate-400">Review and approve the AI's recommended action</p>
        </div>
      </div>

      {/* Decision Summary */}
      {decision && (
        <div className="grid grid-cols-2 gap-3 mb-5">
          <InfoTile icon="🏭" label="Recommended Supplier" value={supplier.supplier_name || '—'} />
          <InfoTile icon="💰" label="Total Cost" value={`$${totalCost.toLocaleString('en-US', { minimumFractionDigits: 2 })}`} />
          <InfoTile icon="📦" label="Quantity" value={`${decision.quantity_to_order?.toLocaleString()} units`} />
          <InfoTile icon="⏱️" label="Lead Time" value={`${supplier.lead_time_days} days`} />
          <InfoTile icon="📍" label="Location" value={supplier.location || '—'} />
          <InfoTile icon="⭐" label="Composite Score" value={`${decision.composite_score?.toFixed(2)} / 10`} />
        </div>
      )}

      {/* Reason */}
      {decision?.reason && (
        <div className="mb-5 p-3 bg-surface-700/50 rounded-xl border border-slate-700/40">
          <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">AI Reasoning</div>
          <p className="text-sm text-slate-300">{decision.reason}</p>
        </div>
      )}

      {/* Comments */}
      <div className="mb-5">
        <label className="text-xs text-slate-400 font-medium block mb-2">Reviewer Comments (optional)</label>
        <textarea
          className="input-field resize-none h-20 text-sm"
          placeholder="Add your review notes here…"
          value={comments}
          onChange={e => setComments(e.target.value)}
        />
      </div>

      {/* Buttons */}
      <div className="flex gap-3">
        <button
          id="approve-btn"
          className="btn-success flex-1 flex items-center justify-center gap-2"
          onClick={() => handleDecision(true)}
          disabled={loading}
        >
          {loading ? '⏳' : '✅'} Approve
        </button>
        <button
          id="reject-btn"
          className="btn-danger flex-1 flex items-center justify-center gap-2"
          onClick={() => handleDecision(false)}
          disabled={loading}
        >
          {loading ? '⏳' : '❌'} Reject
        </button>
      </div>
    </div>
  );
}

function InfoTile({ icon, label, value }) {
  return (
    <div className="bg-surface-700/40 rounded-xl p-3 border border-slate-700/30">
      <div className="text-xs text-slate-500 mb-1">{icon} {label}</div>
      <div className="text-sm font-semibold text-slate-200 truncate">{value}</div>
    </div>
  );
}
