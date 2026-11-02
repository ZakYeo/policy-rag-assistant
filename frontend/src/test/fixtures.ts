import type { AskResponse } from '../contracts/policy';

export const answer: AskResponse = {
  answer: 'Customer data must not be entered into public AI tools.',
  answer_provider: 'openai',
  routing_provider: 'heuristic',
  routing_rationale: 'Relevant policy',
  routed_documents: [{ document_id: 'northstar-ai-acceptable-use-policy', document_name: 'northstar-ai-acceptable-use-policy.pdf', title: 'AI Acceptable Use Policy' }],
  sources: [{ document_name: 'northstar-ai-acceptable-use-policy.pdf', page_number: 1, chunk_id: 'policy-p1-c2' }],
  retrieved_chunks: [{ document_name: 'northstar-ai-acceptable-use-policy.pdf', page_number: 1, chunk_id: 'policy-p1-c2', chunk_index: 2, distance: 0.1, text: 'Do not upload customer lists to public AI tools.' }],
};
