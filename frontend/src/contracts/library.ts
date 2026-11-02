export type ChunkStrategy = 'characters' | 'sentences' | 'paragraphs' | 'html';
export interface ChunkSettings { strategy: ChunkStrategy; size: number; overlap: number; heading_depth: number }
export interface ManagedPolicy {
  id: string; title: string; filename: string; format: string; version: number;
  revision: string | null; settings: ChunkSettings; chunk_count: number; status: string;
}
export interface PolicyContent { text: string; location: string }
export interface PolicyDetail extends ManagedPolicy { content: PolicyContent[] }
export interface PolicyChunk { chunk_id: string; text: string; page_number: number; char_start: number; char_end: number; location?: string }
export interface ChunkPage { total: number; offset: number; items: PolicyChunk[] }
export interface PolicyOperation { id: string; policy_id: string; status: string; stage: string; error: string | null }
export interface LibraryClient {
  upload(file: File): Promise<PolicyOperation>;
  operation(id: string): Promise<PolicyOperation>;
  retry(id: string, version: number): Promise<PolicyOperation>;
  delete(id: string, version: number): Promise<void>;
  rename(id: string, title: string, version: number): Promise<ManagedPolicy>;
  list(): Promise<ManagedPolicy[]>;
  detail(id: string): Promise<PolicyDetail>;
  chunks(id: string, offset: number): Promise<ChunkPage>;
}
export interface LibraryViewModel {
  policies: ManagedPolicy[]; detail: PolicyDetail | null; chunks: ChunkPage | null;
  file: File | null; setFile(file: File | null): void; upload(): Promise<void>; retry(): Promise<void>; operation: PolicyOperation | null;
  confirmDelete: boolean; setConfirmDelete(value: boolean): void; deletePolicy(): Promise<void>;
  title: string; setTitle(title: string): void; rename(): Promise<void>; busy: boolean;
  loading: boolean; error: string | null; tab: 'content' | 'chunks' | 'settings';
  refresh(): Promise<void>; select(id: string): Promise<void>;
  setTab(tab: 'content' | 'chunks' | 'settings'): void;
  loadChunks(offset: number): Promise<void>;
}
