import type { DeskViewModel } from '../contracts/policy';
import { Panel } from './Panel';
import { Skeleton } from './Skeleton';

function Empty({ children }: { children: string }) {
  return <p className="text-muted">{children}</p>;
}

export function Results({ vm }: { vm: DeskViewModel }) {
  return <div className="grid min-w-0 items-start gap-7 min-[960px]:grid-cols-[7fr_5fr] min-[960px]:gap-10" aria-busy={vm.busy}>
    <div className="min-w-0 space-y-7">
      <Panel title="Your answer" meta="Guidance summary" id="answer-title">
        {vm.submittedQuestion && vm.question.trim() !== vm.submittedQuestion &&
          <p className="mb-4 text-sm text-muted [overflow-wrap:anywhere]">Answer for: {vm.submittedQuestion}</p>}
        {vm.status === 'error' && vm.answer && !vm.response && <p className="mb-4 font-semibold text-error">Incomplete answer — the response was interrupted.</p>}
        {vm.answer ? <p className="answer-text reveal whitespace-pre-wrap text-[1.3rem] leading-[1.7] font-medium [overflow-wrap:anywhere]">{vm.answer}</p>
          : vm.busy ? <Skeleton rows={4} /> : <Empty>Ask a question to see guidance from NorthStar’s policies.</Empty>}
        <div className="mt-6 flex items-start gap-2 border-t border-line-subtle pt-4 text-sm text-muted">
          <span aria-hidden="true">ⓘ</span>
          <p>{vm.response?.answer_provider === 'extractive'
            ? 'These extracts come from the retrieved policies. Check the source policy before acting.'
            : 'AI-generated guidance may be inaccurate. Check the source policy before acting.'}</p>
        </div>
      </Panel>
      <Panel title="Supporting passages" meta="Verbatim policy excerpts" id="passages-title">
        {vm.busy && !vm.response ? <Skeleton rows={6} /> : vm.passages.length ? <div className="reveal space-y-4">{vm.passages.map((item) =>
          <blockquote key={item.chunk_id} className="rounded border-l-2 border-accent bg-paper p-4">
            <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2 text-sm">
              <span className="min-w-0 font-semibold text-accent [overflow-wrap:anywhere]">{item.title}</span><span className="text-muted">{item.location || `Page ${item.page_number}`}</span>
            </div><p className="text-base leading-relaxed italic [overflow-wrap:anywhere]">“{item.text}”</p>
          </blockquote>)}</div> : <Empty>{vm.response ? 'No supporting passages were found.' : 'No supporting passages yet.'}</Empty>}
      </Panel>
    </div>
    <aside className="min-w-0 space-y-7" aria-label="Policy evidence">
      <Panel title="Policy references" meta={vm.response ? `${vm.references.length} reference${vm.references.length === 1 ? '' : 's'}` : undefined} id="references-title">
        <p className="mb-4 text-sm text-muted">Source passages supporting this answer:</p>
        {vm.busy && !vm.response ? <Skeleton rows={5} /> : vm.references.length ? <ul className="reveal space-y-3">{vm.references.map((item) =>
          <li key={item.chunk_id} className="rounded border border-line-subtle bg-paper p-4">
            <div className="mb-2 flex flex-wrap items-start justify-between gap-2"><strong className="min-w-0 font-semibold [overflow-wrap:anywhere]">{item.title}</strong>
              <span className="rounded border border-line bg-inset px-2 py-0.5 text-sm text-muted">{item.location || `Page ${item.page_number}`}</span></div>
            <p className="technical-text">{item.document_name}</p><p className="technical-text mt-1">Chunk: {item.chunk_id}</p>
          </li>)}</ul> : <Empty>{vm.response ? 'No references were found for this answer.' : 'No references yet.'}</Empty>}
      </Panel>
      <Panel title="Policies consulted" id="consulted-title">
        {vm.busy && !vm.response ? <Skeleton /> : vm.response?.routed_documents.length ? <ul className="reveal space-y-4">{vm.response.routed_documents.map((doc) =>
          <li key={doc.document_id} className="flex items-start gap-2"><span aria-hidden="true" className="mt-2 size-1.5 shrink-0 rounded-full bg-muted" />
            <div className="min-w-0"><p className="font-semibold [overflow-wrap:anywhere]">{doc.title}</p><p className="technical-text">{doc.document_name}</p></div>
          </li>)}</ul> : <Empty>{vm.response ? 'No policies were selected for this question.' : 'No policies consulted yet.'}</Empty>}
      </Panel>
      <details open className="px-1 text-sm text-muted">
        <summary className="cursor-pointer py-2 font-medium">Technical details</summary>
        {vm.busy && !vm.response ? <Skeleton /> : <dl className="mt-2 space-y-2 rounded border border-line bg-inset p-4">
          <div className="flex justify-between gap-3"><dt>Provider</dt><dd className="text-ink">{vm.response ? vm.response.answer_provider === 'openai' ? 'OpenAI' : 'Extractive' : '—'}</dd></div>
          <div className="flex justify-between gap-3"><dt>Sources</dt><dd className="text-ink">{vm.response?.sources.length ?? '—'}</dd></div>
          <div className="flex justify-between gap-3"><dt>Chunks</dt><dd className="text-ink">{vm.response?.retrieved_chunks.length ?? '—'}</dd></div>
        </dl>}
      </details>
    </aside>
  </div>;
}
