import type { PolicyStreamEvent } from '../contracts/policy';
import { parseResponse, record } from './policyResponse';

function parseFrame(frame: string): PolicyStreamEvent | null {
  let name = '';
  const data: string[] = [];
  for (const line of frame.split(/\r?\n/)) {
    if (line.startsWith(':')) continue;
    const colon = line.indexOf(':');
    if (colon < 0) continue;
    const field = line.slice(0, colon);
    const value = line.slice(colon + 1).replace(/^ /, '');
    if (field === 'event') name = value;
    if (field === 'data') data.push(value);
  }
  if (!data.length) return null;
  let payload: unknown;
  try { payload = JSON.parse(data.join('\n')); }
  catch { throw new Error('The policy service returned an invalid stream. Please try again.'); }
  if (name === 'result') return { type: 'result', response: parseResponse(payload) };
  if (name === 'delta' && record(payload) && typeof payload.text === 'string') return { type: 'delta', text: payload.text };
  if (name === 'error' && record(payload) && typeof payload.message === 'string') throw new Error(payload.message);
  throw new Error('The policy service returned an invalid stream. Please try again.');
}

export async function* readPolicyStream(response: Response): AsyncGenerator<PolicyStreamEvent> {
  if (!response.body) throw new Error('Streaming is unavailable. Please try again.');
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8', { fatal: true });
  let buffer = '';
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });
      let boundary: RegExpExecArray | null;
      while ((boundary = /\r?\n\r?\n/.exec(buffer))) {
        const frame = buffer.slice(0, boundary.index);
        buffer = buffer.slice(boundary.index + boundary[0].length);
        const event = parseFrame(frame);
        if (!event) continue;
        yield event;
        if (event.type === 'result') return;
      }
      if (buffer.length > 1024 * 1024) throw new Error('The policy service returned an invalid stream. Please try again.');
      if (done) break;
    }
    throw new Error('The answer stream was interrupted. Please try again.');
  } finally {
    try { await reader.cancel(); } catch { /* A disconnected body may already be cancelled. */ }
    reader.releaseLock();
  }
}
