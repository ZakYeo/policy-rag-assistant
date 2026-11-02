import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import { usePolicyDesk } from './usePolicyDesk';
import { answer } from '../test/fixtures';

describe('policy question flow', () => {
  test('sample selection fills the draft without submitting or changing the chosen mode', () => {
    const client = { ask: vi.fn(), stream: vi.fn() };
    const focusEditor = vi.fn();
    const { result } = renderHook(() => usePolicyDesk(client, focusEditor));
    act(() => result.current.setProvider('extractive'));
    const sample = result.current.sampleQuestionGroups[0].questions[0];
    act(() => result.current.selectSampleQuestion(sample.id));
    expect(result.current.question).toBe(sample.question);
    expect(result.current.provider).toBe('extractive');
    expect(result.current.status).toBe('idle');
    expect(client.ask).not.toHaveBeenCalled();
    expect(client.stream).not.toHaveBeenCalled();
    expect(focusEditor).toHaveBeenCalledOnce();
  });
  test('validates blank questions without contacting the API', async () => {
    const client = { ask: vi.fn(), stream: vi.fn() };
    const { result } = renderHook(() => usePolicyDesk(client));
    act(() => result.current.setQuestion('   '));
    await act(() => result.current.ask());
    expect(client.ask).not.toHaveBeenCalled();
    expect(result.current.error).toMatch(/enter a question/i);
  });

  test('captures the selected mode and keeps the editor usable during a request', async () => {
    let finish!: (value: typeof answer) => void;
    const client = { ask: vi.fn(() => new Promise<typeof answer>((resolve) => { finish = resolve; })), stream: vi.fn() };
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
    const client = { ask: vi.fn().mockRejectedValueOnce(new Error('Provider unavailable')).mockResolvedValue(answer), stream: vi.fn() };
    const { result } = renderHook(() => usePolicyDesk(client));
    act(() => { result.current.setQuestion('Can I use AI?'); result.current.setProvider('extractive'); });
    await act(() => result.current.ask());
    expect(result.current.error).toBe('Provider unavailable');
    expect(result.current.question).toBe('Can I use AI?');
    await act(() => result.current.ask());
    await waitFor(() => expect(result.current.response?.answer).toBe(answer.answer));
    expect(result.current.error).toBeNull();
  });

  test('shows partial OpenAI text before completion and retains it on failure', async () => {
    let release!: () => void;
    const gate = new Promise<void>((resolve) => { release = resolve; });
    const client = { ask: vi.fn(), async *stream() {
      yield { type: 'delta' as const, text: 'Partial answer' };
      await gate;
      throw new Error('Connection lost');
    } };
    const { result } = renderHook(() => usePolicyDesk(client));
    act(() => result.current.setQuestion('What is the policy?'));
    act(() => { void result.current.ask(); });
    await waitFor(() => expect(result.current.answer).toBe('Partial answer'));
    expect(result.current.busy).toBe(true);
    expect(result.current.response).toBeNull();
    await act(async () => release());
    await waitFor(() => expect(result.current.error).toBe('Connection lost'));
    expect(result.current.answer).toBe('Partial answer');
    expect(result.current.busy).toBe(false);
    expect(client.ask).not.toHaveBeenCalled();
  });

  test('uses the terminal response as the authoritative answer and evidence', async () => {
    const client = { ask: vi.fn(), async *stream() {
      yield { type: 'delta' as const, text: 'First words' };
      yield { type: 'result' as const, response: answer };
    } };
    const { result } = renderHook(() => usePolicyDesk(client));
    act(() => result.current.setQuestion('What is the policy?'));
    await act(() => result.current.ask());
    expect(result.current.answer).toBe(answer.answer);
    expect(result.current.response?.sources).toEqual(answer.sources);
  });

  test('aborts on unmount and closes the generator without publishing later results', async () => {
    let release!: () => void;
    const gate = new Promise<void>((resolve) => { release = resolve; });
    let signal!: AbortSignal;
    let closed = false;
    const client = { ask: vi.fn(), async *stream(_question: string, requestSignal: AbortSignal) {
      signal = requestSignal;
      try {
        yield { type: 'delta' as const, text: 'Partial answer' };
        await gate;
        yield { type: 'result' as const, response: answer };
      } finally { closed = true; }
    } };
    const { result, unmount } = renderHook(() => usePolicyDesk(client));
    act(() => result.current.setQuestion('Question'));
    act(() => { void result.current.ask(); });
    await waitFor(() => expect(result.current.answer).toBe('Partial answer'));
    unmount();
    expect(signal.aborted).toBe(true);
    await act(async () => release());
    await waitFor(() => expect(closed).toBe(true));
    expect(result.current.response).toBeNull();
    expect(result.current.answer).toBe('Partial answer');
  });
});
