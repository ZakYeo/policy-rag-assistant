import type { LibraryClient } from '../contracts/library';

export async function libraryRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, options);
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(typeof payload?.detail === 'string' ? payload.detail : 'The policy request failed. Please try again.');
  }
  return response.json() as Promise<T>;
}
export const libraryClient: LibraryClient = {
  upload: (file) => libraryRequest('/api/policies', { method: 'POST', headers: { 'Content-Type': 'application/octet-stream', 'X-Filename': encodeURIComponent(file.name) }, body: file }),
  operation: (id) => libraryRequest(`/api/operations/${encodeURIComponent(id)}`),
  retry: (id, version) => libraryRequest(`/api/policies/${encodeURIComponent(id)}/retry`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ version }) }),
  delete: (id, version) => libraryRequest(`/api/policies/${encodeURIComponent(id)}`, { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ version }) }),
  rename: (id, title, version) => libraryRequest(`/api/policies/${encodeURIComponent(id)}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title, version }) }),
  list: () => libraryRequest('/api/policies'),
  detail: (id) => libraryRequest(`/api/policies/${encodeURIComponent(id)}`),
  chunks: (id, offset) => libraryRequest(`/api/policies/${encodeURIComponent(id)}/chunks?offset=${offset}`),
};
