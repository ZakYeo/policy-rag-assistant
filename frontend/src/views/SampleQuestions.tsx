import type { SampleQuestionGroup } from '../contracts/sampleQuestions';

export function SampleQuestions({ groups, onSelect }: {
  groups: readonly SampleQuestionGroup[];
  onSelect(id: string): void;
}) {
  return <aside className="sample-panel panel mb-10" aria-labelledby="sample-questions-title">
    <h2 id="sample-questions-title" className="text-lg font-bold">Sample Questions</h2>
    <p className="mt-1 mb-5 text-sm leading-relaxed text-muted">Choose one to fill your question. Edit it before asking if you like.</p>
    <div className="grid gap-5 min-[640px]:grid-cols-2 min-[1840px]:grid-cols-1">
      {groups.map((group) => <section key={group.title} aria-label={group.title}>
        <h3 className="mb-2 text-sm font-semibold text-muted">{group.title}</h3>
        <ul className="space-y-1">
          {group.questions.map((sample) => <li key={sample.id}>
            <button type="button" aria-controls="question" onClick={() => onSelect(sample.id)}
              className="block min-h-10 w-full rounded px-2.5 py-2 text-left text-sm leading-relaxed text-ink hover:bg-inset focus-visible:bg-inset [overflow-wrap:anywhere]">
              {sample.question}
            </button>
          </li>)}
        </ul>
      </section>)}
    </div>
  </aside>;
}
