import type { EvaluationMetadata, EvaluationPassage, EvaluationRow, EvaluationScore, EvaluationViewModel } from '../contracts/evaluation';
import { PageIntro } from './PageIntro';
import { Panel } from './Panel';
import { AnswerText } from './AnswerText';
import { Skeleton } from './Skeleton';

const presetLabel = (preset: string) => preset === 'standard' ? 'Standard · 4 passages' : 'Limited · 1 passage';
const checkLabel = (name: string) => ({ policy_fidelity: 'Policy fidelity', essential_qualifications: 'Essential qualifications', citation_support: 'Citation support', answerability: 'Answerability handling' })[name] || name;
const checkSummary = (name: string) => ({ policy_fidelity: 'Does the answer follow the policy?', essential_qualifications: 'Are required conditions and exceptions included?', citation_support: 'Do the citations support the claims?', answerability: 'Does the answer stay within the available evidence?' })[name] || name;
const number = (value: number | null | undefined) => value == null ? '—' : value.toFixed(3);
const category = (value: string | number | null) => value === 'unable_to_assess' ? 'Unable to assess' : value === 'pass' ? 'Pass' : value === 'fail' ? 'Fail' : value;

function Score({ score }: { score?: EvaluationScore | null }) {
  if (!score) return <span className="text-muted">Not scored</span>;
  return <span>{score.status === 'scored' ? typeof score.value === 'number' ? number(score.value) : category(score.value)
    : score.status === 'not_applicable' ? 'Not applicable' : 'Evaluation error'}</span>;
}

function Passages({ items }: { items: EvaluationPassage[] }) {
  return <div className="space-y-3">{items.map((item, index) => <blockquote key={`${index}-${item.document_name}`} className="rounded border-l-2 border-accent bg-inset p-4">
    <p className="text-sm [overflow-wrap:anywhere]"><code>{item.document_name}</code> · <strong>{item.location || `Page ${item.page_number}`}</strong></p>
    <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed">{item.text}</p>
  </blockquote>)}</div>;
}

function QuestionResult({ row, metadata }: { row: EvaluationRow; metadata: EvaluationMetadata }) {
  return <section className="min-w-0 space-y-4 rounded border border-line p-4">
    <h4 className="font-semibold">{presetLabel(row.preset)}</h4>
    {row.error && <p className="text-error">{row.error}</p>}
    {row.answer && <AnswerText text={row.answer} />}
    <dl className="space-y-2">{Object.entries(metadata.metrics).map(([key, metric]) => <div key={key}>
      <div className="flex justify-between gap-3"><dt>{metric.label}</dt><dd className="font-mono"><Score score={row.metrics[key]} /></dd></div>
      {row.metrics[key]?.reason && <p className="text-sm text-muted">{row.metrics[key].reason}</p>}
      {row.metrics[key]?.trace?.length ? <details className="mt-1 text-sm text-muted"><summary>Inspect judge calculation evidence</summary>
        <pre className="mt-2 whitespace-pre-wrap break-all rounded bg-inset p-3">{JSON.stringify(row.metrics[key].trace, null, 2)}</pre>
      </details> : row.metrics[key]?.status === 'scored' && <p className="text-xs text-muted">Structured judge trace was not recorded for this score.</p>}
    </div>)}</dl>
    <div className="border-t border-line pt-4"><h5 className="mb-3 font-semibold">LLM judge — automated assessment</h5>
      {Object.keys(metadata.checks).map((key) => <div key={key} className="mb-3">
        <p><strong>{checkLabel(key)}:</strong> <Score score={row.checks[key]} /></p>
        <p className="text-sm text-muted">{row.checks[key]?.reason || 'No judgment available.'}</p>
      </div>)}
      <p><strong>Clarity and usefulness:</strong> <Score score={row.clarity} />{row.clarity?.status === 'scored' && ' / 5'}</p>
      <p className="text-sm text-muted">{row.clarity?.reason}</p>
    </div>
    <details><summary className="cursor-pointer font-semibold">Retrieved passages in rank order ({row.chunks.length})</summary>
      <div className="mt-3">{row.chunks.length ? <Passages items={row.chunks} /> : <p className="text-muted">No passages retrieved.</p>}</div>
    </details>
  </section>;
}

export function Evaluation({ vm }: { vm: EvaluationViewModel }) {
  const { run } = vm;
  const historicalCounts = run?.dataset_version === 'northstar-18-v1' ? { case_count: 18, eligible_count: 16 } : {};
  const metadata = vm.metadata && { ...vm.metadata, ...historicalCounts, ...run?.definitions };
  const presets = Object.keys(run?.configuration.presets || { standard: 4 });
  const comparison = presets.length > 1;
  const rows = run?.rows || [];
  const questions = [...new Map(rows.map((row) => [row.case_id, row])).values()].sort((a, b) => (a.level || 0) - (b.level || 0));
  return <main id="main" className="page-width pt-9">
    <PageIntro title="RAG evaluation" description="Explore how retrieval and answer quality are measured. Demo evaluations use reviewed questions and a separate LLM judge." />
    <div className="space-y-7">
      <Panel title="Evaluation runs" meta="Demo feature" id="evaluation-runs">
        <p className="text-muted">Five questions, from a simple lookup to a complex scenario.</p>
        <div className="mt-4 flex flex-wrap gap-2 text-sm">{['5 answers', '5 diagnostic metrics', 'Policy checks + clarity rating'].map(label => <span key={label} className="rounded bg-inset px-3 py-2">{label}</span>)}</div>
        {vm.metadata?.questions && <details className="mt-3 text-sm"><summary>Preview the five questions</summary><ol className="mt-3 list-decimal space-y-2 pl-5">{vm.metadata.questions.map((item) => <li key={item.id}><strong>{item.complexity}:</strong> {item.question}</li>)}</ol></details>}

        <div className="mt-5 flex flex-wrap items-end gap-4">
          <button className="primary-button" disabled={vm.starting || vm.active || !metadata?.configured || vm.loading} onClick={() => void vm.start()}>{vm.starting ? 'Starting…' : vm.active ? 'Evaluation in progress' : 'Run evaluation'}</button>
          {vm.runs.length > 0 && <label className="min-w-0 text-sm font-semibold">Saved run
            <select className="mt-1 block max-w-full rounded border border-line bg-card p-3 text-ink" value={vm.selected} onChange={(event) => vm.select(event.target.value)}>
              {vm.runs.map((item) => <option key={item.id} value={item.id}>{new Date(item.created_at).toLocaleString()} · {item.status}</option>)}
            </select>
          </label>}
        </div>
        <p className="mt-3 text-sm text-muted">Run evaluation uses paid API calls. Viewing saved results is free.</p>
        {metadata && !metadata.configured && <p className="mt-3 text-error">Provider credentials are required before running evaluations.</p>}
        {vm.error && <p role="alert" className="mt-3 text-error">{vm.error}</p>}
        {run && <div className="mt-5" aria-live="polite">
          <p className="font-semibold">{run.status} · {run.progress}/{run.total} answer attempts processed</p>
          {run.status !== 'completed' && <p className="text-sm text-muted">{run.stage}</p>}
          {['queued', 'running'].includes(run.status) && <progress className="mt-2 w-full" aria-label="Evaluation progress" value={run.progress} max={run.total} />}
          {run.error && <p className="mt-2 text-error">{run.error}</p>}
          {run.status === 'partial' && <p className="mt-2 text-error">Some answers or scores could not be produced. Successful results are retained; missing results are excluded from averages.</p>}
          <dl className="mt-4 grid gap-4 rounded bg-inset p-4 text-sm sm:grid-cols-3">
            <div><dt className="text-muted">Answer model</dt><dd className="mt-1 break-all font-mono">{run.configuration.answer_model}</dd></div>
            <div><dt className="text-muted">Judge model</dt><dd className="mt-1 break-all font-mono">{run.configuration.judge_model}</dd></div>
            <div><dt className="text-muted">Reported judge cost · estimate</dt><dd className="mt-1 font-mono">{run.judge_usage && run.configuration.judge_model.startsWith('gpt-5.4-mini') && run.judge_usage.reported_calls > 0
              ? `$${((run.judge_usage.input_tokens * 0.75 + run.judge_usage.output_tokens * 4.5) / 1000000).toFixed(2)}` : 'Not available'}</dd><p className="mt-1 text-xs text-muted">Excludes other API usage.</p></div>
          </dl>
          <details className="mt-4 text-sm"><summary className="cursor-pointer py-2 font-semibold">Usage and technical details</summary>
            <p className="mt-3 text-muted">{run.configuration.human_calibration}</p>
            {run.judge_usage && <>
              <dl className="my-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div><dt className="text-muted">Judge calls</dt><dd className="font-mono">{run.judge_usage.calls}</dd></div>
                <div><dt className="text-muted">Calls with usage</dt><dd className="font-mono">{run.judge_usage.reported_calls}</dd></div>
                <div><dt className="text-muted">Input tokens</dt><dd className="font-mono">{run.judge_usage.input_tokens.toLocaleString()}</dd></div>
                <div><dt className="text-muted">Output tokens</dt><dd className="font-mono">{run.judge_usage.output_tokens.toLocaleString()}</dd></div>
              </dl>
              <p className="text-muted">Estimate uses uncached rates for reported judge tokens. Excludes answer, routing, embedding, preflight and unreported calls; this is not a provider billing total.</p>
            </>}
            <details className="mt-3"><summary className="cursor-pointer py-2">Run configuration and versions</summary><pre className="mt-2 whitespace-pre-wrap break-all rounded bg-inset p-3">{JSON.stringify({ ragas: run.ragas_version, dataset: run.dataset_version, rubric: run.rubric_version, configuration: run.configuration }, null, 2)}</pre></details>
          </details>
        </div>}
        {!vm.loading && !run && !vm.error && <p className="mt-5 text-muted">No saved evaluations yet. Run the benchmark to see real results.</p>}
      </Panel>
      {vm.loading && <Skeleton rows={4} />}
      {metadata && <>
        <section aria-labelledby="diagnostics-heading">
          <h2 id="diagnostics-heading" className="mb-2 text-xl font-bold">Diagnostic metrics</h2>
          <p className="mb-5 text-muted">Scores are evaluation measurements, not percentages of accuracy. {comparison ? 'This historical comparison uses only questions successfully scored in both presets.' : 'Averages include only successfully scored questions; five questions demonstrate the method, not statistical proof of overall accuracy.'} Higher is better for each metric.</p>
          <div className="grid items-start gap-5 min-[800px]:grid-cols-2">{Object.entries(metadata.metrics).map(([key, metric]) => {
            const result = run?.summary[key];
            return <Panel key={key} title={metric.label} meta={`Scale ${metric.range[0]} to ${metric.range[1]}`} id={`metric-${key}`}>
              <p>{metric.explanation}</p>
              <dl className="my-4 grid grid-cols-2 gap-4">
                {presets.map((preset) => <div key={preset}><dt className="text-sm text-muted">{presetLabel(preset)}</dt><dd className="mt-1 font-mono text-2xl">{number(result?.[preset as 'standard' | 'limited'])}</dd></div>)}
              </dl>
              {comparison ? <p className="text-sm text-muted">{result?.paired_count ?? 0}/{metadata.eligible_count} paired questions · Difference (standard − limited): {result?.delta == null ? '—' : `${result.delta > 0 ? '+' : ''}${number(result.delta)}`}</p>
                : <p className="text-sm text-muted">{result?.scored_counts.standard ?? 0}/{metadata.eligible_count} questions scored</p>}
              <p className="mt-1 text-sm text-muted">Missing scores are excluded, never treated as zero.{comparison && ` Scored individually: standard ${result?.scored_counts.standard ?? 0}, limited ${result?.scored_counts.limited ?? 0}.`}</p>
              <div className="mt-4 space-y-2 border-t border-line pt-3 text-sm"><p><strong>Higher:</strong> {metric.higher}</p><p><strong>Lower:</strong> {metric.lower}</p></div>
              <details className="mt-4 border-t border-line pt-2">
                <summary className="cursor-pointer py-2 text-sm font-semibold">Question breakdown · {questions.length} questions</summary>
                <div className="mt-2 space-y-3">{questions.map((question, index) => <div key={question.case_id} className="rounded border border-line p-3">
                  <p className="text-sm font-semibold">{index + 1}. {question.question}</p>
                  {presets.map(preset => {
                    const row = rows.find(item => item.case_id === question.case_id && item.preset === preset);
                    const score = row?.metrics[key];
                    return <div key={preset} className="mt-3 text-sm">
                      <div className="flex flex-wrap items-center justify-between gap-2"><span className="text-muted">{presetLabel(preset)}</span><strong className="font-mono"><Score score={score} /></strong></div>
                      {score?.reason && <p className="mt-2 text-muted">{score.reason}</p>}
                      {row && <details className="mt-2"><summary className="cursor-pointer py-2 text-accent">View answer and evidence</summary>
                        <div className="mt-2 rounded bg-inset p-3">{row.answer ? <AnswerText text={row.answer} /> : <p>No answer available.</p>}</div>
                        {row.error && <p className="mt-2 text-error">{row.error}</p>}
                        <details className="mt-2"><summary className="cursor-pointer py-2">Reviewed reference</summary><p className="mt-2">{row.reference}</p></details>
                        <details className="mt-2"><summary className="cursor-pointer py-2">Retrieved passages ({row.chunks.length})</summary><Passages items={row.chunks} /></details>
                        {score?.trace?.length ? <details className="mt-2"><summary className="cursor-pointer py-2">Judge calculation evidence</summary><pre className="whitespace-pre-wrap break-all rounded bg-inset p-3">{JSON.stringify(score.trace, null, 2)}</pre></details> : null}
                      </details>}
                    </div>;
                  })}
                </div>)}{!questions.length && <p className="text-sm text-muted">Question results will appear as the run progresses.</p>}</div>
              </details>
            </Panel>;
          })}</div>
        </section>
        <Panel title="LLM judge — automated assessment" meta="Policy checks + presentation" id="judge-heading">
          <p className="text-muted">Four policy checks for every answer, plus a separate rating for presentation.</p>
          <details className="mt-3 text-sm"><summary className="cursor-pointer py-2 font-semibold">How to read judge results</summary>
            <dl className="mt-3 grid gap-3 sm:grid-cols-3"><div><dt className="font-semibold">Pass</dt><dd className="text-muted">The criterion was met.</dd></div><div><dt className="font-semibold">Fail</dt><dd className="text-muted">The criterion was not met.</dd></div><div><dt className="font-semibold">Unable to assess</dt><dd className="text-muted">Evidence was insufficient to judge.</dd></div></dl>
            <p className="mt-3 text-muted">A high presentation score cannot cancel a failed policy check. Judges can be wrong; a separate model does not establish independence or human-level accuracy.</p>
          </details>
          {metadata.calibration && <details className="mt-4 rounded border border-line p-4">
            <summary>Developer challenge checks: {metadata.calibration.results.filter((item) => item.agrees).length}/{metadata.calibration.results.length} agree with provisional labels</summary>
            <p className="mt-2 text-sm text-muted">{metadata.calibration.label_status} These separate challenge examples are excluded from benchmark scores. Judge: {metadata.calibration.judge_model} · {new Date(metadata.calibration.created_at).toLocaleString()}.</p>
            <ul className="mt-3 space-y-3 text-sm">{metadata.calibration.results.map((item) => <li key={item.id}><strong>{item.id}</strong>: expected {item.expected}; actual {item.status === 'scored' ? category(item.value) : 'Evaluation error'}.<p className="text-muted">{item.reason}</p></li>)}</ul>
          </details>}
          <div className="mt-5 grid gap-5 min-[800px]:grid-cols-2">{Object.entries(metadata.checks).map(([key, description]) => <div key={key} className="rounded border border-line p-4">
            <h3 className="font-semibold">{checkLabel(key)}</h3><p className="mt-1 text-sm text-muted">{checkSummary(key)}</p>
            {presets.map((preset) => {
              const values = rows.filter((r) => r.preset === preset).map((r) => r.checks[key]);
              const counts = (value: string) => values.filter((v) => v?.status === 'scored' && v.value === value).length;
              const skipped = values.filter((v) => v?.status === 'not_applicable').length;
              const missing = values.filter((v) => !v || v.status === 'error').length;
              return <div key={preset} className="mt-4">
                {comparison && <p className="mb-2 text-sm text-muted">{presetLabel(preset)}</p>}
                <dl className="grid grid-cols-2 gap-3">
                  <div className="rounded bg-inset p-3"><dt className="text-sm text-muted">Pass</dt><dd className="mt-1 font-mono text-2xl">{counts('pass')}</dd></div>
                  <div className="rounded border border-line p-3"><dt className="text-sm text-muted">Fail</dt><dd className={`mt-1 font-mono text-2xl ${counts('fail') ? 'text-error' : ''}`}>{counts('fail')}</dd></div>
                </dl>
                <p className="mt-2 text-xs text-muted">{values.length}/{metadata.case_count} results
                  {counts('unable_to_assess') > 0 && ` · ${counts('unable_to_assess')} unable to assess`}
                  {skipped > 0 && ` · ${skipped} not applicable`}{missing > 0 && ` · ${missing} missing/error`}</p>
              </div>;
            })}
            <details className="mt-3 text-sm"><summary className="cursor-pointer py-2 font-semibold">Criterion and question results</summary>
              <p className="mt-2 text-muted">{description}</p>
              <ul className="mt-3 divide-y divide-line">{rows.map(row => <li key={`${row.case_id}-${row.preset}`} className="py-3">
                <p className="font-semibold">{row.question}</p>
                <p className="mt-1"><Score score={row.checks[key]} />{comparison && ` · ${presetLabel(row.preset)}`}</p>
                <p className="mt-1 text-muted">{row.checks[key]?.reason || 'No judgment available.'}</p>
              </li>)}</ul>
            </details>
          </div>)}</div>
          <h3 className="mt-6 font-semibold">Clarity and usefulness · 1–5 rubric</h3>
          <p className="mt-1 text-sm text-muted">Higher means clearer and more usable. Presentation only; not a correctness score.</p>
          {presets.map(preset => <div key={preset} className="mt-4">
            {comparison && <p className="mb-2 text-sm text-muted">{presetLabel(preset)}</p>}
            <dl className="grid grid-cols-5 gap-2">{[1, 2, 3, 4, 5].map(score => {
              const count = rows.filter(row => row.preset === preset && row.clarity?.status === 'scored' && row.clarity.value === score).length;
              return <div key={score} className={`rounded border border-line p-2 text-center sm:p-4 ${count ? 'bg-inset' : ''}`}><dt className="text-sm text-muted">{score}/5</dt><dd className="mt-2 font-mono text-xl">{count}<span className="mt-1 block font-sans text-xs text-muted">{count === 1 ? 'answer' : 'answers'}</span></dd></div>;
            })}</dl>
            <p className="mt-2 text-xs text-muted">{rows.filter(row => row.preset === preset && row.clarity?.status === 'scored').length}/{metadata.case_count} answers rated</p>
          </div>)}
          <details className="mt-4 text-sm"><summary className="cursor-pointer py-2 font-semibold">View the 1–5 rating rubric</summary><ol className="mt-3 list-decimal space-y-2 pl-5">{Object.values(metadata.clarity_rubric).map(description => <li key={description}>{description}</li>)}</ol></details>
        </Panel>
        <Panel title="Question results" meta={`${questions.length}/${metadata.case_count} questions`} id="question-results">
          <p className="mb-4 text-muted">Inspect each answer alongside its reviewed reference and the evidence actually retrieved. Judge explanations are automated assessments.</p>
          <div className="space-y-3">{questions.map((question) => <details key={question.case_id} className="rounded border border-line p-4">
            <summary className="cursor-pointer font-semibold">{question.level && `${question.level}. `}{question.question} <span className="text-sm font-normal text-muted">· {question.complexity || question.group}</span></summary>
            <div className="mt-4 rounded bg-inset p-4"><h3 className="font-semibold">Reviewed reference answer</h3><p className="mt-2">{question.reference}</p>
              <details className="mt-3"><summary>Reference policy evidence</summary><div className="mt-3"><Passages items={question.reference_contexts} /></div></details>
            </div>
            <div className={`mt-4 grid items-start gap-4 ${comparison ? 'min-[1100px]:grid-cols-2' : ''}`}>{presets.map((preset) => {
              const row = rows.find((r) => r.case_id === question.case_id && r.preset === preset);
              return row ? <QuestionResult key={preset} row={row} metadata={metadata} /> : <p key={preset} className="text-muted">{presetLabel(preset)}: no result yet.</p>;
            })}</div>
          </details>)}</div>
        </Panel>
      </>}
    </div>
  </main>;
}
