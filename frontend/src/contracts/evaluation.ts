export interface EvaluationScore { status: 'scored' | 'error' | 'not_applicable'; value: number | string | null; reason: string; trace?: { task: string; prompt_sha256: string; output: unknown }[] }
export interface EvaluationPassage { document_name: string; page_number: number; text: string; chunk_id?: string; location?: string }
export interface EvaluationRow {
  level?: number; complexity?: string;
  case_id: string; preset: string; question: string; group: string; answerable: boolean;
  reference: string; reference_contexts: EvaluationPassage[]; essential: string;
  answer: string; chunks: EvaluationPassage[]; metrics: Record<string, EvaluationScore>;
  checks: Record<string, EvaluationScore>; clarity: EvaluationScore | null; error: string | null;
}
export interface MetricComparison { standard: number | null; limited: number | null; delta: number | null; paired_count: number; sample_count?: number; scored_counts: Record<string, number> }
export interface EvaluationRun {
  definitions?: Pick<EvaluationMetadata, 'metrics' | 'checks' | 'clarity_rubric' | 'eligible_count' | 'case_count'>;
  id: string; status: string; created_at: string; finished_at: string | null; stage: string;
  progress: number; total: number; error: string | null; dataset_version: string; rubric_version: string;
  ragas_version: string; configuration: { answer_model: string; judge_model: string; human_calibration: string; presets?: Record<string, number>; [key: string]: unknown };
  judge_usage?: { calls: number; reported_calls: number; input_tokens: number; output_tokens: number };
  rows?: EvaluationRow[]; summary: Record<string, MetricComparison>;
}
export interface EvaluationMetadata {
  questions?: { id: string; question: string; level: number; complexity: string }[];
  calibration?: { judge_model: string; rubric_version: string; label_status: string; created_at: string;
    results: { id: string; expected: string; value: string | null; status: string; reason: string; agrees: boolean }[] } | null;
  metrics: Record<string, { label: string; explanation: string; higher: string; lower: string; range: number[] }>;
  checks: Record<string, string>; clarity_rubric: Record<string, string>;
  judge_model: string; answer_model: string; configured: boolean; case_count: number; eligible_count: number;
  dataset_version: string; rubric_version: string;
}
export interface EvaluationClient {
  metadata(signal?: AbortSignal): Promise<EvaluationMetadata>;
  list(signal?: AbortSignal): Promise<EvaluationRun[]>;
  get(id: string, signal?: AbortSignal): Promise<EvaluationRun>;
  start(): Promise<EvaluationRun>;
}
export interface EvaluationViewModel {
  metadata: EvaluationMetadata | null; runs: EvaluationRun[]; run: EvaluationRun | null;
  selected: string; error: string | null; loading: boolean; starting: boolean; active: boolean;
  select(id: string): void; start(): Promise<void>;
}
