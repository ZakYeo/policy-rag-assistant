export type AnswerProvider = 'openai' | 'extractive';
export interface Source { document_name: string; page_number: number; chunk_id: string }
export interface PolicyDocument { document_id: string; document_name: string; title: string }
export interface RetrievedChunk extends Source { chunk_index: number; distance: number; text: string }
export interface AskResponse {
  answer: string;
  answer_provider: AnswerProvider;
  routing_provider: string;
  routing_rationale: string;
  routed_documents: PolicyDocument[];
  sources: Source[];
  retrieved_chunks: RetrievedChunk[];
}
export interface PolicyClient {
  ask(question: string, provider: AnswerProvider, signal: AbortSignal): Promise<AskResponse>;
  stream(question: string, signal: AbortSignal): AsyncIterable<PolicyStreamEvent>;
}
export type PolicyStreamEvent = { type: 'delta'; text: string } | { type: 'result'; response: AskResponse };
export type DeskStatus = 'idle' | 'loading' | 'streaming' | 'success' | 'error';
export interface DeskState {
  question: string;
  provider: AnswerProvider;
  submittedQuestion: string;
  status: DeskStatus;
  answer: string;
  response: AskResponse | null;
  error: string | null;
}
export interface DeskViewModel extends DeskState {
  busy: boolean;
  references: (Source & { title: string })[];
  passages: (RetrievedChunk & { title: string })[];
  setQuestion(value: string): void;
  setProvider(value: AnswerProvider): void;
  ask(): Promise<void>;
}
