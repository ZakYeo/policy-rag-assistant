import type { EvaluationMetadata, EvaluationRun, EvaluationRow } from '../contracts/evaluation';

export const evaluationMetadata: EvaluationMetadata = {
  metrics: Object.fromEntries([
    ['faithfulness', 'Faithfulness'], ['context_precision', 'Context precision'],
    ['context_recall', 'Context recall'], ['answer_relevancy', 'Answer relevancy'], ['factual_correctness', 'Factual correctness'],
  ].map(([key, label]) => [key, { label, explanation: `What ${label.toLowerCase()} measures.`, higher: 'More evidence supported.', lower: 'Less evidence supported.', range: key === 'answer_relevancy' ? [-1, 1] : [0, 1] }])),
  checks: { policy_fidelity: 'No invented policy rules.', essential_qualifications: 'Retain required conditions.', citation_support: 'Citations support claims.', answerability: 'Acknowledge missing information.' },
  clarity_rubric: { score1_description: 'Unusable', score2_description: 'Difficult', score3_description: 'Understandable', score4_description: 'Clear', score5_description: 'Clear and concise' },
  judge_model: 'test-judge', answer_model: 'test-answer', configured: true, case_count: 18, eligible_count: 16, dataset_version: 'test-v1', rubric_version: 'test-v1',
};
const score = { status: 'scored' as const, value: 0.8, reason: '' };
export const evaluationRow: EvaluationRow = {
  case_id: 'customer-data', preset: 'standard', question: 'Can I paste customer data into public AI?', group: 'single-policy', answerable: true,
  reference: 'No. Customer data must not go into public AI.', essential: 'Customer data is prohibited.',
  reference_contexts: [{ document_name: 'policy.pdf', page_number: 1, text: 'Do not upload customer data.' }],
  answer: '**No.** See `policy.pdf`, **Page 1**.', chunks: [{ document_name: 'policy.pdf', page_number: 1, text: 'Do not upload customer data.' }],
  metrics: Object.fromEntries(Object.keys(evaluationMetadata.metrics).map((key) => [key, score])),
  checks: Object.fromEntries(Object.keys(evaluationMetadata.checks).map((key) => [key, { status: 'scored' as const, value: 'pass', reason: 'The cited policy supports the prohibition.' }])),
  clarity: { status: 'scored', value: 5, reason: 'Concise and clear.' }, error: null,
};
export const evaluationRun: EvaluationRun = {
  id: 'saved-run', status: 'completed', created_at: '2026-11-03T12:00:00Z', finished_at: '2026-11-03T12:01:00Z', stage: 'Finished', progress: 36, total: 36, error: null,
  dataset_version: 'test-v1', rubric_version: 'test-v1', ragas_version: '0.4.3',
  configuration: { presets: { standard: 4, limited: 1 }, answer_model: 'test-answer', judge_model: 'test-judge', human_calibration: 'Human calibration pending.' },
  rows: [evaluationRow, { ...evaluationRow, preset: 'limited' }],
  summary: Object.fromEntries(Object.keys(evaluationMetadata.metrics).map((key) => [key, { standard: 0.8, limited: 0.7, delta: 0.1, paired_count: 16, scored_counts: { standard: 16, limited: 16 } }])),
};
