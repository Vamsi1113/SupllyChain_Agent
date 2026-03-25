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
    <div className="h-fit">
      <div className="flex items-center gap-4 mb-8">
        <div className="w-12 h-12 rounded-2xl bg-brand/10 flex items-center justify-center text-2xl shadow-inner">
          🚨
        </div>
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Report Incident</h2>
          <div className="label-text mt-0.5 opacity-60">System Trigger</div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="label-text block mb-3 opacity-80">
            Target Part Context
          </label>
          <input
            type="text"
            className="input-stitch font-mono uppercase text-brand"
            value={partId}
            onChange={(e) => setPartId(e.target.value)}
            placeholder="e.g. PART-001"
            required
            disabled={loading}
          />
        </div>

        <div>
          <label className="label-text block mb-3 opacity-80">
            Disruption Category
          </label>
          <div className="relative">
            <select
              className="input-stitch appearance-none cursor-pointer"
              value={type}
              onChange={(e) => setType(e.target.value)}
              disabled={loading}
            >
              {DISRUPTION_TYPES.map(t => (
                <option key={t.value} value={t.value} className="bg-surface-lowest text-white">
                  {t.label}
                </option>
              ))}
            </select>
            <div className="absolute inset-y-0 right-5 flex items-center pointer-events-none text-brand/40">
              ▼
            </div>
          </div>
        </div>

        <div>
          <label className="label-text block mb-3 opacity-80">
            Resource Requirement
          </label>
          <input
            type="number"
            min="1"
            className="input-stitch"
            value={qty}
            onChange={(e) => setQty(e.target.value)}
            required
            disabled={loading}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="btn-gradient w-full mt-4 flex items-center justify-center gap-3 group"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Syncing...</span>
            </>
          ) : (
            <>
              <span className="group-hover:translate-x-1 transition-transform">🚀</span>
              <span>Execute Orchestration</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
