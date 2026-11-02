import { Skeleton } from './Skeleton';
export const secondaryButton = 'rounded border border-line bg-card px-4 py-2 text-sm font-semibold hover:bg-inset disabled:opacity-50';
export const primaryButton = 'rounded border border-accent bg-accent px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50';
export const fieldStyle = 'mt-1 w-full rounded border border-line bg-paper px-3 py-2 text-ink';

import type { ChunkPage } from '../contracts/library';
export function ChunkList({ page, load }: { page: ChunkPage | null; load(offset: number): Promise<void> }) {
  if (!page) return <Skeleton rows={4} />;
  return <div><p className="mb-4 text-sm text-muted">{page.total} chunks · showing {page.total ? page.offset + 1 : 0}–{Math.min(page.offset + page.items.length, page.total)}</p>
    <ol className="space-y-4">{page.items.map((chunk, index) => <li key={chunk.chunk_id} className="rounded border border-line-subtle bg-paper p-4">
      <div className="mb-2 flex flex-wrap justify-between gap-2 text-sm font-semibold"><span>Chunk {page.offset + index + 1}</span><span className="text-muted">{chunk.location ?? `Page ${chunk.page_number}`} · {chunk.text.length} characters</span></div>
      <p className="whitespace-pre-wrap leading-relaxed [overflow-wrap:anywhere]">{chunk.text}</p><p className="technical-text mt-3">{chunk.chunk_id}</p>
    </li>)}</ol>
    <div className="mt-5 flex gap-3"><button className={secondaryButton} disabled={!page.offset} onClick={() => void load(Math.max(0, page.offset - 20))}>Previous chunks</button><button className={secondaryButton} disabled={page.offset + page.items.length >= page.total} onClick={() => void load(page.offset + 20)}>Next chunks</button></div>
  </div>;
}
