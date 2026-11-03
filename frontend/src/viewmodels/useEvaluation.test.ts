import { act, renderHook, waitFor } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { useEvaluation } from './useEvaluation';
import { evaluationMetadata, evaluationRun } from '../test/evaluationFixtures';
import type { EvaluationClient, EvaluationRun } from '../contracts/evaluation';

function client(): EvaluationClient {
  return { metadata: vi.fn().mockResolvedValue(evaluationMetadata), list: vi.fn().mockResolvedValue([evaluationRun]), get: vi.fn().mockResolvedValue(evaluationRun), start: vi.fn().mockResolvedValue({ ...evaluationRun, id: 'new', status: 'queued', rows: [], progress: 0 }) };
}
test('loads the latest saved evaluation without starting paid work', async () => {
  const api = client();
  const { result } = renderHook(() => useEvaluation(api));
  await waitFor(() => expect(result.current.run?.id).toBe('saved-run'));
  expect(api.start).not.toHaveBeenCalled();
  expect(result.current.loading).toBe(false);
});
test('deduplicates start requests and selects the new run', async () => {
  const api = client();
  let finish!: (run: EvaluationRun) => void;
  api.start = vi.fn(() => new Promise<EvaluationRun>((resolve) => { finish = resolve; }));
  const { result } = renderHook(() => useEvaluation(api));
  await waitFor(() => expect(result.current.loading).toBe(false));
  act(() => { void result.current.start(); void result.current.start(); });
  expect(api.start).toHaveBeenCalledTimes(1);
  await act(async () => finish({ ...evaluationRun, id: 'new', status: 'running' }));
  expect(result.current.selected).toBe('new');
});
test('shows provider and load failures rather than fabricated results', async () => {
  const api = client();
  api.list = vi.fn().mockRejectedValue(new Error('Connection failed'));
  const { result } = renderHook(() => useEvaluation(api));
  await waitFor(() => expect(result.current.error).toBe('Connection failed'));
  expect(result.current.run).toBeNull();
});
test('does not replace a newly selected run with a stale response', async () => {
  const api = client();
  let finishOld!: (run: EvaluationRun) => void;
  api.get = vi.fn((id: string) => id === 'saved-run' ? new Promise<EvaluationRun>((resolve) => { finishOld = resolve; }) : Promise.resolve({ ...evaluationRun, id }));
  const { result } = renderHook(() => useEvaluation(api));
  await waitFor(() => expect(api.get).toHaveBeenCalled());
  act(() => result.current.select('other'));
  await waitFor(() => expect(result.current.run?.id).toBe('other'));
  await act(async () => finishOld(evaluationRun));
  expect(result.current.run?.id).toBe('other');
});
