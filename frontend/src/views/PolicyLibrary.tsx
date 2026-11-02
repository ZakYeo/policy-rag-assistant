import type { LibraryViewModel } from '../contracts/library';
import { Skeleton } from './Skeleton';

export const secondaryButton = 'rounded border border-line bg-card px-4 py-2 text-sm font-semibold hover:bg-inset disabled:opacity-50';
export const primaryButton = 'rounded border border-accent bg-accent px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50';
export const fieldStyle = 'mt-1 w-full rounded border border-line bg-paper px-3 py-2 text-ink';

export function PolicyLibrary({ vm }: { vm: LibraryViewModel }) {
  return <main id="main" className="page-width flex-1 py-10 min-[640px]:py-12">
    <h1 className="text-[1.8rem] font-bold tracking-tight">Manage policies</h1>
    <p className="mt-2 mb-8 text-lg text-muted">Review the policies that inform NorthStar’s guidance.</p>
    {vm.error && <div role="alert" className="mb-6 rounded border border-error bg-error-surface p-4 text-error">{vm.error} <button className="underline" onClick={() => void vm.refresh()}>Refresh policies</button></div>}
    <div className="grid min-w-0 items-start gap-7 min-[960px]:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
      <section aria-labelledby="policies-heading" className="min-w-0 rounded-lg border border-line bg-card p-5 shadow-sm">
        <div className="flex items-center justify-between gap-3 border-b border-line-subtle pb-4"><h2 id="policies-heading" className="text-lg font-bold">Policies</h2><span className="text-sm text-muted">{vm.policies.length} uploaded</span></div>
        {vm.loading && !vm.policies.length ? <Skeleton rows={5} /> : <ul className="mt-3 space-y-2">{vm.policies.map((policy) => <li key={policy.id}>
          <button type="button" onClick={() => void vm.select(policy.id)} aria-current={vm.detail?.id === policy.id ? 'true' : undefined}
            className={`w-full rounded border p-3 text-left [overflow-wrap:anywhere] hover:bg-inset ${vm.detail?.id === policy.id ? 'border-accent bg-inset' : 'border-transparent'}`}>
            <strong className="block font-semibold">{policy.title}</strong><span className="technical-text mt-1 block">{policy.filename}</span>
            <span className="mt-2 block text-sm text-muted">{policy.format.toUpperCase()} · {policy.chunk_count} chunks · {policy.status}</span>
          </button>
        </li>)}</ul>}
        {!vm.loading && !vm.policies.length && <p className="mt-4 text-muted">No policies uploaded yet.</p>}
      </section>
      <section aria-label="Selected policy" aria-busy={vm.loading} className="min-w-0 rounded-lg border border-line bg-card p-5 min-[640px]:p-7 shadow-sm">
        {vm.loading ? <Skeleton rows={7} /> : vm.detail ? <>
          <h2 className="text-xl font-bold [overflow-wrap:anywhere]">{vm.detail.title}</h2>
          <p className="technical-text mt-2">{vm.detail.filename}</p>
          <form className="mt-5 flex flex-wrap items-end gap-3" onSubmit={(event) => { event.preventDefault(); void vm.rename(); }}>
            <label className="min-w-0 flex-1 text-sm font-semibold">Display title<input className={fieldStyle} value={vm.title} maxLength={160} required disabled={vm.busy} onChange={(event) => vm.setTitle(event.target.value)} /></label>
            <button type="submit" disabled={vm.busy || !vm.title.trim() || vm.title.trim() === vm.detail.title} className={secondaryButton}>Save title</button>
          </form>
          <a className="mt-3 inline-block text-sm font-semibold text-accent underline" href={`/api/policies/${encodeURIComponent(vm.detail.id)}/original`}>Download original</a>
          <div className="mt-5">
            {vm.confirmDelete ? <div role="group" aria-label="Confirm policy deletion" className="rounded border border-error bg-error-surface p-4">
              <p className="text-error [overflow-wrap:anywhere]">Delete “{vm.detail.title}”? Its file and chunks will be removed from future answers.</p>
              <div className="mt-3 flex flex-wrap gap-3"><button className={secondaryButton} disabled={vm.busy} onClick={() => void vm.deletePolicy()}>Confirm delete</button><button className={secondaryButton} disabled={vm.busy} onClick={() => vm.setConfirmDelete(false)}>Cancel</button></div>
            </div> : <button className={`${secondaryButton} text-error`} disabled={vm.busy} onClick={() => vm.setConfirmDelete(true)}>Delete policy</button>}
          </div>
          <div className="my-6 flex flex-wrap gap-2 border-b border-line pb-3" aria-label="Policy sections">
            {(['content', 'chunks', 'settings'] as const).map((tab) => <button key={tab} type="button" aria-pressed={vm.tab === tab} className={`${secondaryButton} ${vm.tab === tab ? 'border-accent text-accent' : ''}`} onClick={() => vm.setTab(tab)}>{tab === 'content' ? 'Content' : tab === 'chunks' ? 'Chunks' : 'Chunking settings'}</button>)}
          </div>
          {vm.tab === 'content' && <div className="space-y-6">{vm.detail.content.length ? vm.detail.content.map((page, index) => <section key={index}><h3 className="mb-2 text-sm font-semibold text-muted">{page.location}</h3><p className="whitespace-pre-wrap leading-relaxed [overflow-wrap:anywhere]">{page.text}</p></section>) : <p className="text-muted">Content will appear after processing.</p>}</div>}
          {vm.tab === 'chunks' && <ChunkList page={vm.chunks} load={vm.loadChunks} />}
          {vm.tab === 'settings' && <dl className="space-y-3 text-sm"><div>Strategy: {vm.detail.settings.strategy}</div><div>Maximum size: {vm.detail.settings.size} characters</div><div>Overlap: {vm.detail.settings.overlap} characters</div></dl>}
        </> : <div className="py-12 text-center"><h2 className="text-lg font-semibold">Select a policy</h2><p className="mt-2 text-muted">Read its content and inspect the chunks used for answers.</p></div>}
      </section>
    </div>
  </main>;
}

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
