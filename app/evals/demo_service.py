"""Evaluate the live application pipeline, retaining every actual result."""
import asyncio
import hashlib
from importlib.metadata import version

from app.assistant import AssistantService
from app.evals.demo_dataset import DATASET_VERSION, SOURCE_HASHES, load_cases
from app.evals.demo_metrics import DemoScorer, RUBRIC_VERSION, summarize
from app.evals.demo_store import now

PRESETS = {'standard': 4, 'limited': 1}


class LibraryChanged(ValueError):
    pass


def fingerprint(library):
    with library.store.lock:
        return [{k: policy[k] for k in ('id', 'filename', 'revision', 'version', 'status')}
                for policy in library.store.list()]


def validate_sources(library):
    policies = {p['filename']: p for p in library.store.list()}
    for filename, expected in SOURCE_HASHES.items():
        p = policies.get(filename)
        if not p or p['status'] != 'ready' or not p['revision']:
            raise ValueError(f'Benchmark policy not ready: {filename}')
        if hashlib.sha256(library.store.original(p['id']).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Benchmark policy content changed: {filename}. Update references first.')


def create_run(store, library, settings):
    if not settings.openai_api_key:
        raise ValueError('Configure OPENAI_API_KEY before running paid evaluations.')
    if settings.eval_judge_model == settings.openai_chat_model:
        raise ValueError('Configure EVAL_JUDGE_MODEL separately from the answer model.')
    load_cases(settings.documents_dir)
    with library.store.lock:
        validate_sources(library)
        policies = fingerprint(library)
    return store.create({
        'dataset_version': DATASET_VERSION, 'rubric_version': RUBRIC_VERSION,
        'ragas_version': version('ragas'), 'policy_fingerprint': policies,
        'configuration': {'answer_model': settings.openai_chat_model, 'judge_model': settings.eval_judge_model,
            'judge_embedding_model': settings.openai_embedding_model, 'router_provider': settings.router_provider,
            'embedding_provider': settings.embedding_provider, 'presets': PRESETS,
            'factual_correctness': {'mode': 'f1', 'atomicity': 'low', 'coverage': 'low'},
            'answer_relevancy_strictness': 3, 'judge_max_tokens': 4096,
            'judge_temperature': 1.0 if settings.eval_judge_model.startswith('gpt-6') else 'RAGAS model default',
            'human_calibration': 'Pending: fixtures are developer-reviewed, not human calibration.'},
    })


async def execute_run(store, run, library, settings, scorer=None, assistant=None):
    """Injection points keep automated tests offline; production uses actual RAGAS."""
    client = None
    try:
        run.update(status='running', stage='Checking judge access')
        store.save(run)
        if scorer is None:
            from openai import AsyncOpenAI
            from ragas.llms import llm_factory
            from ragas.embeddings.base import embedding_factory
            from ragas.metrics import DiscreteMetric
            client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=60, max_retries=0)
            llm = llm_factory(settings.eval_judge_model, client=client, max_tokens=4096, max_retries=1)
            preflight = DiscreteMetric(name='preflight', allowed_values=['pass', 'fail'],
                                      prompt='Return pass if the statement is true: {statement}')
            result = await asyncio.wait_for(preflight.ascore(llm=llm, statement='2 + 2 = 4'), 90)
            if result.value != 'pass':
                raise ValueError('Judge preflight failed')
            embeddings = embedding_factory('openai', model=settings.openai_embedding_model, client=client)
            scorer = DemoScorer(llm, embeddings)
        cases = load_cases(settings.documents_dir)
        run['total'] = len(cases) * len(PRESETS)
        assistant = assistant or AssistantService(library=library)
        expected = run['policy_fingerprint']

        def unchanged():
            if fingerprint(library) != expected:
                raise LibraryChanged('Policy library changed during evaluation. Start a new comparison on stable revisions.')

        # Parallelism across two cases keeps progress useful without flooding the provider.
        semaphore = asyncio.Semaphore(2)

        async def evaluate(case, preset, top_k):
            async with semaphore:
                unchanged()
                run['stage'] = f"Evaluating {case['id']} ({preset})"
                store.save(run)
                row = {'case_id': case['id'], 'preset': preset, 'question': case['question'],
                       'group': case['group'], 'answerable': case['answerable'],
                       'reference': case['reference'], 'reference_contexts': case['reference_contexts'],
                       'essential': case['essential'], 'answer': '', 'chunks': [], 'metrics': {},
                       'checks': {}, 'clarity': None, 'error': None}
                try:
                    # Route + retrieve under the short snapshot lock; never hold it over generation.
                    def prepare():
                        with library.store.lock:
                            unchanged()
                            prepared = assistant._prepare(case['question'], top_k, 'openai')
                            unchanged()
                            return prepared
                    prepared = await asyncio.to_thread(prepare)
                    result = await asyncio.wait_for(asyncio.to_thread(
                        prepared.answerer.answer, prepared.question, prepared.chunks), 90)
                    response = assistant._response(prepared, result)
                    unchanged()
                    row.update(answer=response.answer, chunks=response.retrieved_chunks,
                               answer_provider=response.answer_provider, routing_provider=response.routing_provider)
                    if response.answer_provider != 'openai':
                        raise ValueError('Expected OpenAI answer provider')
                    row.update(await scorer.score(case, response.answer, response.retrieved_chunks))
                except LibraryChanged:
                    raise
                except Exception as exc:
                    row['error'] = f'Case failed ({type(exc).__name__}).'
                run['rows'].append(row)
                run['progress'] = len(run['rows'])
                run['summary'] = summarize(run['rows'])
                store.save(run)
                unchanged()

        tasks = [asyncio.create_task(evaluate(case, preset, k)) for case in cases for preset, k in PRESETS.items()]
        try:
            await asyncio.gather(*tasks)
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        unchanged()
        errors = any(r['error'] or any(m['status'] == 'error' for m in [*r['metrics'].values(), *r['checks'].values(), *([r['clarity']] if r['clarity'] else [])]) for r in run['rows'])
        run.update(status='partial' if errors else 'completed', stage='Finished', finished_at=now())
    except LibraryChanged as exc:
        run.update(status='invalidated', stage='Policies changed', error=str(exc), finished_at=now(), summary={})
    except Exception as exc:
        run.update(status='failed', stage='Evaluation failed',
                   error=f'Evaluation failed ({type(exc).__name__}). Check judge model access, credentials and provider availability. No model was substituted.', finished_at=now())
    finally:
        if client:
            await client.close()
        store.save(run)


def run_in_background(store, run, library, settings):
    asyncio.run(execute_run(store, run, library, settings))
