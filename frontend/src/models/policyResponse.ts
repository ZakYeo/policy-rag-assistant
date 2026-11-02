import type { AskResponse } from '../contracts/policy';

export function record(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}
function strings(value: Record<string, unknown>, keys: string[]) {
  return keys.every((key) => typeof value[key] === 'string');
}
function source(value: unknown) {
  return record(value) && strings(value, ['document_name', 'chunk_id'])
    && Number.isInteger(value.page_number) && Number(value.page_number) > 0;
}
export function parseResponse(value: unknown): AskResponse {
  if (!record(value) || !strings(value, ['answer', 'routing_provider', 'routing_rationale'])
      || !['openai', 'extractive'].includes(String(value.answer_provider))
      || !Array.isArray(value.sources) || !value.sources.every(source)
      || !Array.isArray(value.routed_documents) || !value.routed_documents.every((doc: unknown) =>
        record(doc) && strings(doc, ['document_id', 'document_name', 'title']))
      || !Array.isArray(value.retrieved_chunks) || !value.retrieved_chunks.every((chunk: unknown) =>
        source(chunk) && record(chunk) && typeof chunk.text === 'string'
        && Number.isInteger(chunk.chunk_index) && Number(chunk.chunk_index) >= 0
        && typeof chunk.distance === 'number' && Number.isFinite(chunk.distance))) {
    throw new Error('The policy service returned an invalid response. Please try again.');
  }
  return value as unknown as AskResponse;
}
