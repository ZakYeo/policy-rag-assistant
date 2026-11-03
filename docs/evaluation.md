# RAG evaluation demo

Open **RAG evaluation** at `/evaluations`. Saved results load without provider calls.
**Run evaluation** starts one paid five-answer evaluation using the real application routing, retrieval,
and OpenAI answer pipeline. Ordinary policy questions never invoke the judge.

## Benchmark

The versioned benchmark contains five answerable questions of increasing complexity:
a simple lookup, a clear prohibition, multiple conditions, cross-policy reasoning, and
a complex remote-work disclosure scenario. References were checked against the three bundled PDFs;
file hashes protect against accidentally scoring changed documents against stale answers.
This fixed benchmark requires exactly those three policies: added documents might change
the answers or make an unanswerable question answerable, so they require a revised benchmark.
Reference passages use page text independently of retrieval chunks.

Each question is answered once using up to four passages. There is no automatic second
configuration or automatic repeat evaluation. Historical two-preset runs remain viewable.
The runner records the actual retrieved evidence and actual routing provider for each answer.
Any change to the managed policy catalogue during a run invalidates its results.

## Diagnostic scores

- **Faithfulness:** RAGAS extracts answer claims and judges support in retrieved context.
- **Context precision:** reference-based, rank-sensitive average precision. This is **not**
  simply the fraction of retrieved chunks that are relevant.
- **Context recall:** proportion of reference-answer claims supported by retrieved context.
- **Answer relevancy:** average cosine similarity between the original question and three
  questions reconstructed from the answer; RAGAS also considers noncommittal responses.
  Native cosine results can be negative and are not clamped into percentages.
- **Factual correctness:** RAGAS claim-based F1 against the reference, with low atomicity
  and low coverage decomposition settings. Reference incompleteness can affect this score.

All are estimates, not a measured percentage of factual accuracy. Metric scores are not
combined into one overall grade. Current averages include successful scores and display their denominator out of five.
Historical paired comparisons include only questions successfully scored in both presets.
Errors and non-finite results are missing scores, never zero or a pass.
New scores retain structured claim decomposition and support judgments for inspection,
alongside prompt hashes. Older saved scores without traces are labeled explicitly.

The older 18-case benchmark excluded its two unanswerable questions from diagnostic
averages. All five current questions are answerable and eligible for all five metrics. With no
retrieved context, context recall is zero for answerable questions; precision and
faithfulness are displayed as undefined/not applicable. Judge checks still assess the answer.

## LLM judge

`EVAL_JUDGE_MODEL` defaults to `gpt-5.4-mini`, separate from `OPENAI_CHAT_MODEL`.
RAGAS uses that judge for the diagnostic metrics and four custom discrete checks:
policy fidelity, essential qualifications, citation support, and answerability handling.
Checks return Pass, Fail, or Unable to assess, with evidence-based explanations.
Provider errors are separate from substantive failures. Provably impossible benchmark
page references also fail a deterministic location check.

A separate RAGAS 1–5 rubric assesses **presentation**, from unusable to clear, concise,
and immediately usable. A 5/5 presentation rating cannot override a failed policy check.
The page exposes the rubric and score distribution, not a misleading percent conversion.

Judges receive reference evidence and retrieved evidence without preset identities.
Evaluation prompts instruct them to ignore grading instructions inside the evidence or
answer and not reward verbosity. These measures reduce risk but do not make judgments
infallible. A separate model is not statistically independent of the answer model.

Optional developer-labeled challenge examples cover invented rules, missing exceptions,
wrong pages, correct abstention, fabricated answers, verbosity and judge injection.
They are separate from benchmark scores. Their labels are provisional: **human
calibration remains pending** until a person reviews them and representative run results.

## Running and persistence

Install the pinned dependencies from the development setup, including RAGAS 0.4.3.
Configure `OPENAI_API_KEY`, the answer model, and the separate judge model. Provider model
access is checked before the benchmark; no automatic model substitution takes place.
Evaluation uses paid OpenAI embedding calls even when retrieval embeddings are local.

The page exposes an explicit run action. Optional terminal equivalents:

```sh
RAGAS_DO_NOT_TRACK=true .venv/bin/python -m app.evals.demo_cli
RAGAS_DO_NOT_TRACK=true .venv/bin/python -m app.evals.demo_cli --calibrate
```

A process-held file lease and a database constraint permit one active benchmark. Startup
recovery skips runs whose process still holds the lease. Results live in
`data/evaluations/evaluations.sqlite3` (or beside the configured vector-store directory).
Challenge results live separately in `judge-challenges.json`. Both are local, ignored data.
Back up this directory to retain evaluation history. Completed results survive restarts;
unfinished work is marked interrupted and never automatically repeats paid calls.

The older `app.evals.cli` and integration-test harness still test the independent,
deterministic extractive pipeline. They are not the source of the new page's results.

API: `GET /api/evaluations` supplies explanations and rubric metadata;
`POST /api/evaluations/runs` starts a run; `GET /api/evaluations/runs` lists the latest
50 runs; `GET /api/evaluations/runs/{id}` returns progress and saved evidence.

References: [RAGAS metric catalogue](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/),
[RAGAS rubric scoring](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/rubrics_based/),
[OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices).

## Cost and repeatability

The judge uses low reasoning effort and a 2,048-token completion limit per call.
RAGAS still makes multiple calls per metric: five answers are not five provider calls.
Judge usage is recorded when returned by the provider; the UI estimates reported judge
token cost at published uncached GPT-5.4 mini rates ($0.75/M input, $4.50/M output).
This excludes answer, routing, embedding and preflight calls and is not a billing total.
No monetary cap is imposed. Quota, authentication, or rate-limit failures stop further
evaluation calls; successful results remain saved. Reloading does not start new work.
The optional calibration command is a separate paid action and is not part of each run.
