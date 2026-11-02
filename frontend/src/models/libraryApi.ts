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
  list: () => libraryRequest('/api/policies'),
  detail: (id) => libraryRequest(`/api/policies/${encodeURIComponent(id)}`),
  chunks: (id, offset) => libraryRequest(`/api/policies/${encodeURIComponent(id)}/chunks?offset=${offset}`),
};
