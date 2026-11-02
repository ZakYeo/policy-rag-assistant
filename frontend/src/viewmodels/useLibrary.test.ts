import { renderHook, act, waitFor } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { useLibrary } from './useLibrary';
import type { LibraryClient, PolicyDetail } from '../contracts/library';

test('loads a policy and its content; selection fetches its actual chunks', async () => {
  const detail: PolicyDetail = { id: 'policy', title: 'Policy', filename: 'policy.pdf', format: 'pdf', version: 1, revision: 'r1', settings: { strategy: 'characters', size: 900, overlap: 150, heading_depth: 2 }, chunk_count: 1, status: 'ready', content: [{ text: 'Actual policy text', location: 'Page 1' }] };
  const client: LibraryClient = { delete: vi.fn(), rename: vi.fn(), list: vi.fn().mockResolvedValue([detail]), detail: vi.fn().mockResolvedValue(detail), chunks: vi.fn().mockResolvedValue({ items: [{ text: 'Actual chunk' }], offset: 0, total: 1 }) };
  const { result } = renderHook(() => useLibrary(client));
  await waitFor(() => expect(result.current.loading).toBe(false));
  await act(() => result.current.select('policy'));
  expect(result.current.detail?.content[0].text).toBe('Actual policy text');
  expect(result.current.chunks?.total).toBe(1);
});
