import React, { useState } from 'react';

const DISRUPTION_TYPES = [
  { value: 'supplier_failure', label: 'Supplier Failure' },
  { value: 'logistics_delay', label: 'Logistics Delay' },
  { value: 'quality_issue', label: 'Quality Issue' },
  { value: 'demand_spike', label: 'Demand Spike' },
  { value: 'geopolitical', label: 'Geopolitical Risk' },
  { value: 'natural_disaster', label: 'Natural Disaster' },
];

export default function IncidentCard({ onSubmit, loading }) {
  const [partId, setPartId] = useState('PART-001');
  const [type, setType] = useState('supplier_failure');
  const [qty, setQty] = useState(100);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!partId) return;
    onSubmit({
      part_id: partId.toUpperCase(),
      disruption_type: type,
      quantity_needed: parseInt(qty, 10),
      priority: 'high',
    });
  };

  return (
    <div className="glass-card p-6 h-fit sticky top-6 border-t-2 border-t-brand-500/50">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-brand-500/20 flex items-center justify-center text-xl">
          🚨
        </div>
        <div>
          <h2 className="text-lg font-bold text-slate-100">Report Incident</h2>
          <p className="text-sm text-slate-400">Trigger multi-agent response</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Target Part ID
          </label>
          <input
            type="text"
            className="input-field font-mono uppercase"
            value={partId}
            onChange={(e) => setPartId(e.target.value)}
            placeholder="e.g. PART-001"
            required
            disabled={loading}
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Disruption Type
          </label>
          <div className="relative">
            <select
              className="select-field"
              value={type}
              onChange={(e) => setType(e.target.value)}
              disabled={loading}
            >
              {DISRUPTION_TYPES.map(t => (
                <option key={t.value} value={t.value} className="bg-surface-800">
                  {t.label}
                </option>
              ))}
            </select>
            <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none text-slate-400">
              ▼
            </div>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Quantity Required
          </label>
          <input
            type="number"
            min="1"
            className="input-field"
            value={qty}
            onChange={(e) => setQty(e.target.value)}
            required
            disabled={loading}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="btn-primary w-full mt-2 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Initializing...
            </>
          ) : '🚀 Auto-Resolve'}
        </button>
      </form>
    </div>
  );
}
