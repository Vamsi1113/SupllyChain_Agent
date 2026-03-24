const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * Start a new supply chain orchestration run.
 * @param {Object} payload - { part_id, disruption_type, quantity_needed, priority, notes }
 * @returns {Promise<{ run_id: string, status: string, message: string }>}
 */
export async function startRun(payload) {
  return apiFetch('/run-agent', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Get current status and agent logs for a run.
 * @param {string} runId
 * @returns {Promise<StatusResponse>}
 */
export async function getStatus(runId) {
  return apiFetch(`/status/${runId}`);
}

/**
 * Approve or reject a pending action.
 * @param {string} runId
 * @param {boolean} approved
 * @param {string} comments
 * @returns {Promise<Object>}
 */
export async function submitApproval(runId, approved, comments = '') {
  return apiFetch('/approve', {
    method: 'POST',
    body: JSON.stringify({ run_id: runId, approved, reviewer_comments: comments }),
  });
}

/**
 * List all active runs (debug endpoint).
 * @returns {Promise<{ total: number, runs: Array }>}
 */
export async function listRuns() {
  return apiFetch('/runs');
}
