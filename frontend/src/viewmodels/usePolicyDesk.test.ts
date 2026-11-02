import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import { usePolicyDesk } from './usePolicyDesk';
import { answer } from '../test/fixtures';

describe('policy question flow', () => {
  test('validates blank questions without contacting the API', async () => {
    const client = { ask: vi.fn() };
    const { result } = renderHook(() => usePolicyDesk(client));
    act(() => result.current.setQuestion('   '));
    await act(() => result.current.ask());
    expect(client.ask).not.toHaveBeenCalled();
    expect(result.current.error).toMatch(/enter a question/i);
  });

  test('captures the selected mode and keeps the editor usable during a request', async () => {
    let finish!: (value: typeof answer) => void;
    const client = { ask: vi.fn(() => new Promise<typeof answer>((resolve) => { finish = resolve; })) };
    const { result } = renderHook(() => usePolicyDesk(client));
    act(() => { result.current.setQuestion('  What is the rule? '); result.current.setProvider('extractive'); });
    act(() => { void result.current.ask(); });
    expect(result.current.busy).toBe(true);
    act(() => result.current.setQuestion('My next question'));
    act(() => { void result.current.ask(); });
    expect(client.ask).toHaveBeenCalledTimes(1);
    expect(client.ask.mock.calls[0].slice(0, 2)).toEqual(['What is the rule?', 'extractive']);
    await act(async () => finish({ ...answer, answer_provider: 'extractive' }));
    expect(result.current.question).toBe('My next question');
    expect(result.current.submittedQuestion).toBe('What is the rule?');
    expect(result.current.response?.sources).toEqual(answer.sources);
    expect(result.current.busy).toBe(false);
  });

  test('shows provider errors, preserves question text and allows resubmission', async () => {
    const client = { ask: vi.fn().mockRejectedValueOnce(new Error('Provider unavailable')).mockResolvedValue(answer) };
    const { result } = renderHook(() => usePolicyDesk(client));
    act(() => result.current.setQuestion('Can I use AI?'));
    await act(() => result.current.ask());
    expect(result.current.error).toBe('Provider unavailable');
    expect(result.current.question).toBe('Can I use AI?');
    await act(() => result.current.ask());
    await waitFor(() => expect(result.current.response?.answer).toBe(answer.answer));
    expect(result.current.error).toBeNull();
  });
});
