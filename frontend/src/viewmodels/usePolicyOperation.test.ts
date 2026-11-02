import { act, renderHook } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { usePolicyOperation } from './usePolicyOperation';
import type { LibraryClient } from '../contracts/library';

test('keeps tracking an operation through a transient polling failure', async () => {
  vi.useFakeTimers();
  try {
    const operation = { id: 'job', policy_id: 'policy', status: 'running', stage: 'Indexing', error: null };
    const operationRequest = vi.fn().mockRejectedValueOnce(new Error('Temporary connection failure')).mockResolvedValueOnce({ ...operation, status: 'succeeded', stage: 'Ready for questions' });
    const completed = vi.fn().mockResolvedValue(undefined);
    const client = { operation: operationRequest } as unknown as LibraryClient;
    const { result } = renderHook(() => usePolicyOperation(client, completed));
    act(() => result.current.track(operation));
    await act(async () => { await vi.advanceTimersByTimeAsync(700); });
    expect(result.current.pending).toBe(true);
    expect(result.current.connectionError).toContain('Temporary');
    await act(async () => { await vi.advanceTimersByTimeAsync(2000); });
    expect(completed).toHaveBeenCalledWith(expect.objectContaining({ status: 'succeeded' }));
    expect(result.current.pending).toBe(false);
  } finally { vi.useRealTimers(); }
});
