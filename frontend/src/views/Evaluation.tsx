import type { EvaluationMetadata, EvaluationPassage, EvaluationRow, EvaluationScore, EvaluationViewModel } from '../contracts/evaluation';
import { PageIntro } from './PageIntro';
import { Panel } from './Panel';
import { AnswerText } from './AnswerText';
import { Skeleton } from './Skeleton';

const presetLabel = (preset: string) => preset === 'standard' ? 'Standard · 4 passages' : 'Limited · 1 passage';
const checkLabel = (name: string) => ({ policy_fidelity: 'Policy fidelity', essential_qualifications: 'Essential qualifications', citation_support: 'Citation support', answerability: 'Answerability handling' })[name] || name;
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
        <p className="text-muted">Five questions, five answers: progress from a simple policy lookup to a complex cross-policy scenario. Each answer uses up to four retrieved passages and receives all five diagnostic metrics plus judge checks.</p>
        {vm.metadata?.questions && <details className="mt-3 text-sm"><summary>Preview the five questions</summary><ol className="mt-3 list-decimal space-y-2 pl-5">{vm.metadata.questions.map((item) => <li key={item.id}><strong>{item.complexity}:</strong> {item.question}</li>)}</ol></details>}
        <p className="mt-2 text-sm text-muted">Running an evaluation makes paid answer, judge, and embedding calls using the configured provider account. Normal policy questions do not trigger evaluation.</p>
        <div className="mt-5 flex flex-wrap items-end gap-4">
          <button className="primary-button" disabled={vm.starting || vm.active || !metadata?.configured || vm.loading} onClick={() => void vm.start()}>{vm.starting ? 'Starting…' : vm.active ? 'Evaluation in progress' : 'Run evaluation'}</button>
          {vm.runs.length > 0 && <label className="min-w-0 text-sm font-semibold">Saved run
            <select className="mt-1 block max-w-full rounded border border-line bg-card p-3 text-ink" value={vm.selected} onChange={(event) => vm.select(event.target.value)}>
              {vm.runs.map((item) => <option key={item.id} value={item.id}>{new Date(item.created_at).toLocaleString()} · {item.status}</option>)}
            </select>
          </label>}
        </div>
        {metadata && !metadata.configured && <p className="mt-3 text-error">Provider credentials are required before running evaluations.</p>}
        {vm.error && <p role="alert" className="mt-3 text-error">{vm.error}</p>}
        {run && <div className="mt-5" aria-live="polite">
          <p className="font-semibold">{run.status} · {run.progress}/{run.total} answer attempts processed</p>
          <p className="text-sm text-muted">{run.stage}</p>
          {['queued', 'running'].includes(run.status) && <progress className="mt-2 w-full" aria-label="Evaluation progress" value={run.progress} max={run.total} />}
          {run.error && <p className="mt-2 text-error">{run.error}</p>}
          {run.status === 'partial' && <p className="mt-2 text-error">Some answers or scores could not be produced. Successful results are retained; missing results are excluded from averages.</p>}
          <p className="mt-3 text-sm text-muted [overflow-wrap:anywhere]">Answer: <code>{run.configuration.answer_model}</code> · Judge: <code>{run.configuration.judge_model}</code> · RAGAS {run.ragas_version}</p>
          <p className="text-sm text-muted">{run.configuration.human_calibration}</p>
          {run.judge_usage && <p className="mt-2 text-sm text-muted">Judge metric calls: {run.judge_usage.calls}. Token usage reported for {run.judge_usage.reported_calls} calls: {run.judge_usage.input_tokens.toLocaleString()} input, {run.judge_usage.output_tokens.toLocaleString()} output.
            {run.configuration.judge_model.startsWith('gpt-5.4-mini') && run.judge_usage.reported_calls > 0 && <> Uncached-rate estimate for reported judge usage: ${((run.judge_usage.input_tokens * 0.75 + run.judge_usage.output_tokens * 4.5) / 1000000).toFixed(2)}.</>} Excludes answer, routing, embedding and preflight calls; this is not a provider billing total.</p>}
          <details className="mt-3 text-sm"><summary>Run configuration and versions</summary><pre className="mt-2 whitespace-pre-wrap break-all rounded bg-inset p-3">{JSON.stringify({ dataset: run.dataset_version, rubric: run.rubric_version, configuration: run.configuration }, null, 2)}</pre></details>
        </div>}
        {!vm.loading && !run && !vm.error && <p className="mt-5 text-muted">No saved evaluations yet. Run the benchmark to see real results.</p>}
      </Panel>
      {vm.loading && <Skeleton rows={4} />}
      {metadata && <>
        <section aria-labelledby="diagnostics-heading">
          <h2 id="diagnostics-heading" className="mb-2 text-xl font-bold">Diagnostic metrics</h2>
          <p className="mb-5 text-muted">Scores are evaluation measurements, not percentages of accuracy. {comparison ? 'This historical comparison uses only questions successfully scored in both presets.' : 'Averages include only successfully scored questions; five questions demonstrate the method, not statistical proof of overall accuracy.'} Higher is better for each metric.</p>
          <div className="grid gap-5 min-[800px]:grid-cols-2">{Object.entries(metadata.metrics).map(([key, metric]) => {
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
            </Panel>;
          })}</div>
        </section>
        <Panel title="LLM judge — automated assessment" meta="Policy checks + presentation" id="judge-heading">
          <p className="text-muted">Each critical requirement is assessed separately. Pass means the criterion was met; Fail means it was not. Unable to assess means the evaluation evidence was insufficient. A high presentation score cannot cancel a failed policy check.</p>
          <p className="mt-2 text-sm text-muted">Judges can be wrong. Using a separate model does not establish independence or human-level accuracy. Review the evidence and explanations below.</p>
          {metadata.calibration && <details className="mt-4 rounded border border-line p-4">
            <summary>Developer challenge checks: {metadata.calibration.results.filter((item) => item.agrees).length}/{metadata.calibration.results.length} agree with provisional labels</summary>
            <p className="mt-2 text-sm text-muted">{metadata.calibration.label_status} These separate challenge examples are excluded from benchmark scores. Judge: {metadata.calibration.judge_model} · {new Date(metadata.calibration.created_at).toLocaleString()}.</p>
            <ul className="mt-3 space-y-3 text-sm">{metadata.calibration.results.map((item) => <li key={item.id}><strong>{item.id}</strong>: expected {item.expected}; actual {item.status === 'scored' ? category(item.value) : 'Evaluation error'}.<p className="text-muted">{item.reason}</p></li>)}</ul>
          </details>}
          <div className="mt-5 grid gap-5 min-[800px]:grid-cols-2">{Object.entries(metadata.checks).map(([key, description]) => <div key={key} className="rounded border border-line p-4">
            <h3 className="font-semibold">{checkLabel(key)}</h3><p className="mt-1 text-sm text-muted">{description}</p>
            {presets.map((preset) => {
              const values = rows.filter((r) => r.preset === preset).map((r) => r.checks[key]);
              const counts = (value: string) => values.filter((v) => v?.status === 'scored' && v.value === value).length;
              const skipped = values.filter((v) => v?.status === 'not_applicable').length;
              const missing = values.filter((v) => !v || v.status === 'error').length;
              return <p key={preset} className="mt-3 text-sm"><strong>{presetLabel(preset)}:</strong> {counts('pass')} pass · {counts('fail')} fail · {counts('unable_to_assess')} unable to assess · {skipped} not applicable · {missing} missing/error ({values.length}/{metadata.case_count} results)</p>;
            })}
          </div>)}</div>
          <h3 className="mt-6 font-semibold">Clarity and usefulness · 1–5 rubric</h3>
          <p className="mt-1 text-sm text-muted">Higher means clearer, more usable presentation. This is not a correctness score. We show the distribution rather than interpreting ordinal ratings as percentages.</p>
          <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm">{Object.values(metadata.clarity_rubric).map((description) => <li key={description}>{description}</li>)}</ol>
          {presets.map((preset) => <p key={preset} className="mt-3 text-sm"><strong>{presetLabel(preset)}:</strong> {[1, 2, 3, 4, 5].map((score) => `${score}/5: ${rows.filter((r) => r.preset === preset && r.clarity?.status === 'scored' && r.clarity.value === score).length}`).join(' · ')} · {rows.filter((r) => r.preset === preset && r.clarity?.status === 'scored').length}/{metadata.case_count} rated</p>)}
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
