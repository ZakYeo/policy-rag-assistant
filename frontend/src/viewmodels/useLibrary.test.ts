import { renderHook, act, waitFor } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { useLibrary } from './useLibrary';
import type { LibraryClient, PolicyDetail } from '../contracts/library';

test('loads a policy and its content; selection fetches its actual chunks', async () => {
  const detail: PolicyDetail = { id: 'policy', title: 'Policy', filename: 'policy.pdf', format: 'pdf', version: 1, revision: 'r1', settings: { strategy: 'characters', size: 900, overlap: 150, heading_depth: 2 }, chunk_count: 1, status: 'ready', content: [{ text: 'Actual policy text', location: 'Page 1' }] };
  const client: LibraryClient = { preview: vi.fn(), previewChunks: vi.fn(), apply: vi.fn(), upload: vi.fn(), operation: vi.fn(), retry: vi.fn(), delete: vi.fn(), rename: vi.fn(), list: vi.fn().mockResolvedValue([detail]), detail: vi.fn().mockResolvedValue(detail), chunks: vi.fn().mockResolvedValue({ items: [{ text: 'Actual chunk' }], offset: 0, total: 1 }) };
  const { result } = renderHook(() => useLibrary(client));
  await waitFor(() => expect(result.current.loading).toBe(false));
  await act(() => result.current.select('policy'));
  expect(result.current.detail?.content[0].text).toBe('Actual policy text');
  expect(result.current.chunks?.total).toBe(1);
});

test('a changed setting invalidates its preview and cannot apply unseen changes', async () => {
  const detail: PolicyDetail = { id: 'policy', title: 'Policy', filename: 'policy.pdf', format: 'pdf', version: 1, revision: 'r1', settings: { strategy: 'characters', size: 900, overlap: 150, heading_depth: 2 }, chunk_count: 1, status: 'ready', content: [{ text: 'Policy text', location: 'Page 1' }] };
  const client: LibraryClient = { preview: vi.fn().mockResolvedValue({ id: 'preview', version: 1, settings: detail.settings, chunks: { items: [], offset: 0, total: 0 } }), previewChunks: vi.fn(), apply: vi.fn(), upload: vi.fn(), operation: vi.fn(), retry: vi.fn(), delete: vi.fn(), rename: vi.fn(), list: vi.fn().mockResolvedValue([detail]), detail: vi.fn().mockResolvedValue(detail), chunks: vi.fn().mockResolvedValue({ items: [], offset: 0, total: 0 }) };
  const { result } = renderHook(() => useLibrary(client));
  await waitFor(() => expect(result.current.loading).toBe(false));
  await act(() => result.current.select('policy'));
  await act(() => result.current.previewChunks());
  expect(result.current.preview?.id).toBe('preview');
  act(() => result.current.setSettings({ ...detail.settings, size: 500 }));
  expect(result.current.preview).toBeNull();
  await act(() => result.current.applyPreview());
  expect(client.apply).not.toHaveBeenCalled();
});

test('reattaches to a persisted processing operation when the library loads', async () => {
  const detail: PolicyDetail = { id: 'policy', title: 'Policy', filename: 'policy.txt', format: 'txt', version: 1, revision: 'r1', settings: { strategy: 'characters', size: 900, overlap: 150, heading_depth: 2 }, chunk_count: 1, status: 'ready', content: [] };
  const operation = { id: 'persisted', policy_id: 'policy', status: 'running', stage: 'Indexing', error: null };
  const client: LibraryClient = { preview: vi.fn(), previewChunks: vi.fn(), apply: vi.fn(), upload: vi.fn(), retry: vi.fn(), delete: vi.fn(), rename: vi.fn(),
    list: vi.fn().mockResolvedValueOnce([{ ...detail, status: 'processing', operation_id: 'persisted' }]).mockResolvedValue([detail]),
    operation: vi.fn().mockResolvedValueOnce(operation).mockResolvedValue({ ...operation, status: 'succeeded' }),
    detail: vi.fn().mockResolvedValue(detail), chunks: vi.fn().mockResolvedValue({ items: [], offset: 0, total: 0 }) };
  const { result } = renderHook(() => useLibrary(client));
  await waitFor(() => expect(result.current.operation?.id).toBe('persisted'));
  await waitFor(() => expect(result.current.detail?.id).toBe('policy'), { timeout: 3000 });
  await waitFor(() => expect(result.current.busy).toBe(false));
});
