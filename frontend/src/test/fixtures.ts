import type { AskResponse } from '../contracts/policy';

export const answer: AskResponse = {
  answer: "No. NorthStar's AI Acceptable Use Policy prohibits entering customer data into public AI tools. Use only approved tools and the minimum data necessary. Review the applicable policy before proceeding.",
  answer_provider: 'openai',
  routing_provider: 'heuristic',
  routing_rationale: 'Relevant policy',
  routed_documents: [
    { document_id: 'northstar-ai-acceptable-use-policy', document_name: 'northstar-ai-acceptable-use-policy.pdf', title: 'AI Acceptable Use Policy' },
    { document_id: 'northstar-information-security-policy', document_name: 'northstar-information-security-policy.pdf', title: 'Information Security and Data Handling Policy' },
  ],
  sources: [
    { document_name: 'northstar-ai-acceptable-use-policy.pdf', page_number: 1, chunk_id: 'northstar-ai-acceptable-use-policy-p1-c2' },
    { document_name: 'northstar-ai-acceptable-use-policy.pdf', page_number: 2, chunk_id: 'northstar-ai-acceptable-use-policy-p2-c0' },
  ],
  retrieved_chunks: [
    { document_name: 'northstar-ai-acceptable-use-policy.pdf', page_number: 1, chunk_id: 'northstar-ai-acceptable-use-policy-p1-c2', chunk_index: 2, distance: 0.1, text: 'Confidential, restricted, personal, customer, financial, security-sensitive, and unreleased product information must not be entered into any unapproved AI tool.' },
    { document_name: 'northstar-ai-acceptable-use-policy.pdf', page_number: 2, chunk_id: 'northstar-ai-acceptable-use-policy-p2-c0', chunk_index: 0, distance: 0.2, text: 'Do not upload contracts, HR records, customer lists, credentials, source code, or incident details to public AI tools.' },
  ],
};
