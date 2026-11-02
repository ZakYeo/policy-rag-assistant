import { expect, test, vi } from 'vitest';
import { readPolicyStream } from './policyStream';
import { answer } from '../test/fixtures';
import type { PolicyStreamEvent } from '../contracts/policy';

const encode = (event: string, data: unknown) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
function response(text: string, byteSize = 1) {
  const bytes = new TextEncoder().encode(text);
  return new Response(new ReadableStream({ start(controller) {
    for (let offset = 0; offset < bytes.length; offset += byteSize) controller.enqueue(bytes.slice(offset, offset + byteSize));
    controller.close();
  } }), { headers: { 'Content-Type': 'text/event-stream' } });
}

test('parses fragmented Unicode, comments, CRLF frames and the terminal response', async () => {
  const text = ': keepalive\r\n\r\n' + encode('delta', { text: 'Café 👋' }).replaceAll('\n', '\r\n') + encode('result', answer);
  const events: PolicyStreamEvent[] = [];
  for await (const event of readPolicyStream(response(text))) events.push(event);
  expect(events).toEqual([{ type: 'delta', text: 'Café 👋' }, { type: 'result', response: answer }]);
});

test('preserves delivered deltas and reports interruption when no completion arrives', async () => {
  const events: PolicyStreamEvent[] = [];
  await expect(async () => {
    for await (const event of readPolicyStream(response(encode('delta', { text: 'Partial' })))) events.push(event);
  }).rejects.toThrow(/interrupted/i);
  expect(events).toEqual([{ type: 'delta', text: 'Partial' }]);
});

test('handles explicit errors and rejects malformed data safely', async () => {
  for (const [frame, message] of [
    [encode('error', { message: 'Provider unavailable' }), 'Provider unavailable'],
    ['event: delta\ndata: not-json\n\n', 'invalid stream'],
    [encode('result', { answer: 'missing evidence' }), 'invalid response'],
  ]) {
    await expect(async () => { for await (const event of readPolicyStream(response(frame))) void event; }).rejects.toThrow(new RegExp(message, 'i'));
  }
});

test('stops after the first terminal result and cancels the body reader', async () => {
  const cancel = vi.fn();
  const body = new ReadableStream({ start(controller) {
    controller.enqueue(new TextEncoder().encode(encode('result', answer) + encode('delta', { text: 'duplicate' })));
  }, cancel });
  const events: PolicyStreamEvent[] = [];
  for await (const event of readPolicyStream(new Response(body))) events.push(event);
  expect(events).toEqual([{ type: 'result', response: answer }]);
  expect(cancel).toHaveBeenCalled();
});
