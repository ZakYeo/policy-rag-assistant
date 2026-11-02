import type { DeskViewModel } from '../contracts/policy';

export function PolicyDesk({ vm }: { vm: DeskViewModel }) {
  return <>
    <header><strong>NorthStar</strong> / Policy Desk</header>
    <main>
      <h1>Ask about NorthStar policies</h1>
      <p>Search workplace standards across information security, acceptable AI use, confidentiality, and data handling.</p>
      <form onSubmit={(event) => { event.preventDefault(); void vm.ask(); }}>
        <label htmlFor="question">Your question</label>
        <textarea id="question" value={vm.question} onChange={(event) => vm.setQuestion(event.target.value)} />
        <fieldset><legend>Answer style</legend>
          <label><input type="radio" name="provider" checked={vm.provider === 'openai'} onChange={() => vm.setProvider('openai')} />AI-assisted (OpenAI)</label>
          <label><input type="radio" name="provider" checked={vm.provider === 'extractive'} onChange={() => vm.setProvider('extractive')} />Direct policy extracts (Extractive)</label>
        </fieldset>
        <button disabled={vm.busy}>{vm.busy ? 'Checking policies…' : 'Ask a question'}</button>
      </form>
      {vm.error && <p role="alert">{vm.error}</p>}
      <section aria-busy={vm.busy}>
        <h2>Your answer</h2><p>{vm.answer || (vm.busy ? 'Checking policies…' : 'Your answer will appear here.')}</p>
        <h2>Policy references</h2>
        {vm.references.map((item) => <div key={item.chunk_id}>{item.title} · Page {item.page_number}<p>{item.document_name}</p><p>{item.chunk_id}</p></div>)}
        <h2>Supporting passages</h2>
        {vm.passages.map((item) => <blockquote key={item.chunk_id}>{item.title} · Page {item.page_number}<p>{item.text}</p></blockquote>)}
        <h2>Policies consulted</h2>
        {vm.response?.routed_documents.map((doc) => <p key={doc.document_id}>{doc.title} — {doc.document_name}</p>)}
        <details open><summary>Technical details</summary>
          <p>Provider: {vm.response?.answer_provider ?? '—'} · Sources: {vm.response?.sources.length ?? '—'} · Chunks: {vm.response?.retrieved_chunks.length ?? '—'}</p>
        </details>
      </section>
    </main>
  </>;
}
