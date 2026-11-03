"""Evaluate the live application pipeline, retaining every actual result."""
import asyncio
import hashlib
from importlib.metadata import version

from app.assistant import AssistantService
from app.evals.demo_dataset import DATASET_VERSION, SOURCE_HASHES, load_cases
from app.evals.demo_metrics import DemoScorer, RUBRIC_VERSION, summarize, METRICS, CHECKS, CLARITY, make_judge, provider_failure
from app.evals.demo_store import now

PRESETS = {'standard': 4}


class LibraryChanged(ValueError):
    pass


class ProviderUnavailable(RuntimeError):
    pass


def fingerprint(library):
    with library.store.lock:
        return [{k: policy[k] for k in ('id', 'filename', 'revision', 'version', 'status')}
                for policy in library.store.list()]


def validate_sources(library):
    policies = {p['filename']: p for p in library.store.list()}
    if set(policies) != set(SOURCE_HASHES):
        raise ValueError('This fixed benchmark requires exactly the three sample policies. Additional policies may change the reference answers; update the benchmark before evaluating a different corpus.')
    for filename, expected in SOURCE_HASHES.items():
        p = policies.get(filename)
        if not p or p['status'] != 'ready' or not p['revision']:
            raise ValueError(f'Benchmark policy not ready: {filename}')
        if hashlib.sha256(library.store.original(p['id']).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Benchmark policy content changed: {filename}. Update references first.')


def create_run(store, library, settings):
    from app.retrieval.answerer import _messages
    if not settings.openai_api_key:
        raise ValueError('Configure OPENAI_API_KEY before running paid evaluations.')
    if settings.eval_judge_model == settings.openai_chat_model:
        raise ValueError('Configure EVAL_JUDGE_MODEL separately from the answer model.')
    cases = load_cases(settings.documents_dir)
    with library.store.lock:
        validate_sources(library)
        policies = fingerprint(library)
    return store.create({
        'dataset_version': DATASET_VERSION, 'rubric_version': RUBRIC_VERSION,
        'total': len(cases),
        'ragas_version': version('ragas'), 'policy_fingerprint': policies,
        'definitions': {'metrics': METRICS, 'checks': CHECKS, 'clarity_rubric': CLARITY, 'eligible_count': len(cases), 'case_count': len(cases)},
        'configuration': {'answer_model': settings.openai_chat_model, 'judge_model': settings.eval_judge_model,
            'answer_prompt_sha256': hashlib.sha256(_messages('', [])[0]['content'].encode()).hexdigest(),
            'judge_embedding_model': settings.openai_embedding_model, 'router_provider': settings.router_provider,
            'embedding_provider': settings.embedding_provider, 'presets': PRESETS,
            'factual_correctness': {'mode': 'f1', 'atomicity': 'low', 'coverage': 'low'},
            'answer_relevancy_strictness': 3,
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
            from ragas.embeddings.base import embedding_factory
            from ragas.metrics import DiscreteMetric
            client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=60, max_retries=0)
            llm = make_judge(client, settings.eval_judge_model)
            run['configuration']['judge_parameters'] = llm._map_provider_params()
            store.save(run)
            preflight = DiscreteMetric(name='preflight', allowed_values=['pass', 'fail'],
                                      prompt='Return pass if the statement is true: {statement}')
            result = await asyncio.wait_for(preflight.ascore(llm=llm, statement='2 + 2 = 4'), 90)
            if result.value != 'pass':
                raise ValueError('Judge preflight failed')
            embeddings = embedding_factory('openai', model=settings.openai_embedding_model, client=client)
            scorer = DemoScorer(llm, embeddings)
            scorer.llm.usage.update(run.get('judge_usage', {}))
        cases = load_cases(settings.documents_dir)
        run['total'] = len(cases) * len(PRESETS)
        assistant = assistant or AssistantService(library=library)
        expected = run['policy_fingerprint']

        def unchanged():
            if fingerprint(library) != expected:
                raise LibraryChanged('Policy library changed during evaluation. Start a new comparison on stable revisions.')

        # Five cases, sequentially: stop before further spending on provider failures.
        async def evaluate(case, preset, top_k):
            unchanged()
            run['stage'] = f"Evaluating {case['id']} ({preset})"
            store.save(run)
            row = {'case_id': case['id'], 'preset': preset, 'question': case['question'],
                   'level': case.get('level'), 'complexity': case.get('complexity', case['group']),
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
                row['provider_error'] = provider_failure(exc)
                row['error'] = row['provider_error'] or f'Case failed ({type(exc).__name__}).'
            run['rows'].append(row)
            run['progress'] = len(run['rows'])
            run['summary'] = summarize(run['rows'], tuple(PRESETS))
            run['judge_usage'] = dict(getattr(getattr(scorer, 'llm', None), 'usage', {}))
            store.save(run)
            unchanged()
            if row.get('provider_error'):
                raise ProviderUnavailable(row['provider_error'])

        for case in cases:
            for preset, top_k in PRESETS.items():
                if any(row['case_id'] == case['id'] and row['preset'] == preset for row in run['rows']):
                    continue
                await evaluate(case, preset, top_k)
        unchanged()
        errors = any(r['error'] or any(m['status'] == 'error' for m in [*r['metrics'].values(), *r['checks'].values(), *([r['clarity']] if r['clarity'] else [])]) for r in run['rows'])
        run.update(status='partial' if errors else 'completed', stage='Finished', finished_at=now())
    except ProviderUnavailable as exc:
        run.update(status='partial' if run['rows'] else 'failed', stage='Stopped: provider unavailable', error=str(exc), finished_at=now())
    except LibraryChanged as exc:
        run.update(status='invalidated', stage='Policies changed', error=str(exc), finished_at=now(), summary={})
    except Exception as exc:
        run.update(status='failed', stage='Evaluation failed',
                   error=provider_failure(exc) or f'Evaluation failed ({type(exc).__name__}). Check judge model access, credentials and provider availability. No model was substituted.', finished_at=now())
    finally:
        try:
            if client:
                await client.close()
        finally:
            store.save(run)


def run_in_background(store, run, library, settings):
    asyncio.run(execute_run(store, run, library, settings))
