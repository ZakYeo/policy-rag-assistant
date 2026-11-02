import { expect, test, vi } from 'vitest';
import { createPolicyApi } from './policyApi';
import { answer } from '../test/fixtures';

test('sends the existing API contract and validates its response', async () => {
  const fetcher = vi.fn().mockResolvedValue(Response.json(answer));
  const api = createPolicyApi(fetcher);
  const response = await api.ask('A question', 'extractive', new AbortController().signal);
  expect(response).toEqual(answer);
  expect(JSON.parse(fetcher.mock.calls[0][1].body)).toEqual({ question: 'A question', answer_provider: 'extractive' });
});

test('rejects malformed payloads and displays safe HTTP errors', async () => {
  const fetcher = vi.fn().mockResolvedValueOnce(Response.json({ answer: 'Missing evidence' }))
    .mockResolvedValueOnce(Response.json({ detail: 'OpenAI is not configured.' }, { status: 503 }));
  const api = createPolicyApi(fetcher);
  await expect(api.ask('Question', 'openai', new AbortController().signal)).rejects.toThrow(/invalid response/i);
  await expect(api.ask('Question', 'openai', new AbortController().signal)).rejects.toThrow('OpenAI is not configured.');
});
