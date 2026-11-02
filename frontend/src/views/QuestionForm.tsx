import type { DeskViewModel } from '../contracts/policy';

export function QuestionForm({ vm }: { vm: DeskViewModel }) {
  return <section className="panel mb-10" aria-label="Ask a policy question">
    <form onSubmit={(event) => { event.preventDefault(); void vm.ask(); }}>
      <label htmlFor="question" className="mb-2 block font-semibold">Your question</label>
      <textarea id="question" rows={3} value={vm.question}
        placeholder="Type your question about company policies…"
        className="min-h-32 w-full resize-y rounded border border-line bg-paper p-4 text-lg leading-relaxed placeholder:text-muted focus:border-accent"
        onChange={(event) => vm.setQuestion(event.target.value)} />
      <div className="mt-6 flex flex-wrap items-center justify-between gap-5 border-t border-line-subtle pt-4">
        <fieldset className="min-w-0">
          <legend className="sr-only">Answer style</legend>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
          <span aria-hidden="true" className="text-sm font-semibold text-muted">Answer style:</span>
          <label className="flex cursor-pointer items-center gap-2 text-base">
            <input type="radio" name="provider" value="openai" checked={vm.provider === 'openai'}
              onChange={() => vm.setProvider('openai')} className="size-4 shrink-0 accent-accent" />
            AI-assisted (OpenAI)
          </label>
          <label className="flex cursor-pointer items-center gap-2 text-base">
            <input type="radio" name="provider" value="extractive" checked={vm.provider === 'extractive'}
              onChange={() => vm.setProvider('extractive')} className="size-4 shrink-0 accent-accent" />
            Direct policy extracts (Extractive)
          </label>
          </div>
        </fieldset>
        <button type="submit" disabled={vm.busy} className="primary-button w-full min-[640px]:w-auto">
          {vm.busy ? 'Checking policies…' : 'Ask a question'}
        </button>
      </div>
    </form>
  </section>;
}
