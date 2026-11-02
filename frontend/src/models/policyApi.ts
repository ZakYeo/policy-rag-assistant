import type { AnswerProvider, PolicyClient } from '../contracts/policy';
import { parseResponse, record } from './policyResponse';
import { readPolicyStream } from './policyStream';

async function checkStatus(response: Response) {
  if (response.ok) return;
  let payload: unknown;
  try { payload = await response.json(); } catch { /* Non-JSON gateway errors use a safe fallback. */ }
  throw new Error(record(payload) && typeof payload.detail === 'string'
    ? payload.detail : 'Unable to check policies right now. Please try again.');
}
const request = (question: string, provider: AnswerProvider, signal: AbortSignal): RequestInit => ({
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ question, answer_provider: provider }), signal,
});

export function createPolicyApi(fetcher: typeof fetch = fetch): PolicyClient {
  return {
    async ask(question, provider, signal) {
      const response = await fetcher('/api/ask', request(question, provider, signal));
      await checkStatus(response);
      return parseResponse(await response.json());
    },
    async *stream(question, signal) {
      const response = await fetcher('/api/ask/stream', request(question, 'openai', signal));
      await checkStatus(response);
      if (!response.headers.get('content-type')?.includes('text/event-stream')) {
        throw new Error('The policy service returned an invalid stream. Please try again.');
      }
      yield* readPolicyStream(response);
    },
  };
}
