import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.evals.demo_dataset import load_cases
from app.evals.demo_service import execute_run, fingerprint
from app.evals.demo_store import RunStore, RunConflict


class FakeLibrary:
    def __init__(self):
        self.policies = [{'id': 'p', 'filename': 'p.pdf', 'revision': 'r1', 'version': 1, 'status': 'ready'}]
        self.store = SimpleNamespace(lock=threading.RLock(), list=lambda: self.policies)


class FakeAssistant:
    def _prepare(self, question, top_k, provider):
        return SimpleNamespace(question=question, chunks=[], answerer=SimpleNamespace(answer=lambda q, c: 'answer'))

    def _response(self, prepared, result):
        return SimpleNamespace(answer=result, retrieved_chunks=[], answer_provider='openai', routing_provider='heuristic')


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = RunStore(Path(self.temp.name))
        self.library = FakeLibrary()

    def test_single_active_run_and_restart_recovery(self):
        run = self.store.create({})
        with self.assertRaises(RunConflict):
            RunStore(Path(self.temp.name)).create({})
        self.store.recover()
        self.assertEqual(self.store.get(run['id'])['status'], 'interrupted')
        self.store.create({})

    async def test_execution_persists_and_uses_real_preset_values(self):
        run = self.store.create({'policy_fingerprint': fingerprint(self.library)})
        seen = []
        class Scorer:
            async def score(self, case, answer, chunks):
                return {'metrics': {}, 'checks': {}, 'clarity': {'status': 'scored', 'value': 4, 'reason': 'clear'}}
        assistant = FakeAssistant()
        original = assistant._prepare
        def prepare(q, k, p):
            seen.append((k, p))
            return original(q, k, p)
        assistant._prepare = prepare
        cases = load_cases(Path('documents'))[:1]
        with patch('app.evals.demo_service.load_cases', return_value=cases):
            await execute_run(self.store, run, self.library, SimpleNamespace(documents_dir=Path('documents')), Scorer(), assistant)
        saved = self.store.get(run['id'])
        self.assertEqual(saved['status'], 'completed')
        self.assertEqual(saved['progress'], 2)
        self.assertEqual(set(seen), {(4, 'openai'), (1, 'openai')})
        self.assertEqual(len(saved['rows']), 2)

    async def test_policy_mutation_invalidates_comparison(self):
        run = self.store.create({'policy_fingerprint': fingerprint(self.library)})
        library = self.library
        class Scorer:
            async def score(self, *args):
                library.policies[0]['version'] = 2
                return {'metrics': {}, 'checks': {}, 'clarity': None}
        with patch('app.evals.demo_service.load_cases', return_value=load_cases(Path('documents'))[:1]):
            await execute_run(self.store, run, library, SimpleNamespace(documents_dir=Path('documents')), Scorer(), FakeAssistant())
        saved = self.store.get(run['id'])
        self.assertEqual(saved['status'], 'invalidated')
        self.assertEqual(saved['summary'], {})

    async def test_provider_failure_is_visible_and_not_success(self):
        run = self.store.create({'policy_fingerprint': fingerprint(self.library)})
        class Broken(FakeAssistant):
            def _prepare(self, *args):
                raise RuntimeError('sensitive provider detail')
        with patch('app.evals.demo_service.load_cases', return_value=load_cases(Path('documents'))[:1]):
            await execute_run(self.store, run, self.library, SimpleNamespace(documents_dir=Path('documents')), object(), Broken())
        saved = self.store.get(run['id'])
        self.assertEqual(saved['status'], 'partial')
        self.assertTrue(all(r['error'] for r in saved['rows']))
        self.assertNotIn('sensitive provider detail', str(saved))

    def test_list_omits_large_evidence_payload(self):
        self.store.create({'policy_fingerprint': ['private-internal-data']})
        listed = self.store.list()[0]
        self.assertNotIn('rows', listed)
        self.assertNotIn('policy_fingerprint', listed)
