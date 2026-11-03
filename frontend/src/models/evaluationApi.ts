import type { EvaluationClient } from '../contracts/evaluation';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/evaluations${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : 'Unable to load evaluation results.');
  }
  return response.json();
}
export const evaluationClient: EvaluationClient = {
  metadata: (signal) => request('', { signal }),
  list: (signal) => request('/runs', { signal }),
  get: (id, signal) => request(`/runs/${encodeURIComponent(id)}`, { signal }),
  start: () => request('/runs', { method: 'POST' }),
};
