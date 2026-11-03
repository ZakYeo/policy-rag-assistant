import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.evals.demo_store import RunStore
from app.evals.routes import get_store
from app.main import create_app
from app.policies.library import get_library


class EvaluationApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = RunStore(Path(self.temp.name))
        self.app = create_app()
        self.app.dependency_overrides[get_store] = lambda: self.store
        self.app.dependency_overrides[get_library] = lambda: object()

    def test_saved_runs_metadata_and_direct_page(self):
        with TestClient(self.app) as client:
            self.assertEqual(client.get('/evaluations').status_code, 200)
            self.assertEqual(client.get('/api/evaluations/runs').json(), [])
            self.assertEqual(client.get('/api/evaluations/runs/missing').status_code, 404)
            metadata = client.get('/api/evaluations').json()
            self.assertEqual(len(metadata['metrics']), 5)
            self.assertEqual(metadata['eligible_count'], 5)
            self.assertEqual(metadata['metrics']['answer_relevancy']['range'], [-1, 1])

    def test_explicit_start_and_same_origin_protection(self):
        with TestClient(self.app) as client, patch('app.evals.demo_service.create_run', side_effect=lambda store, *args: store.create({})), patch('app.evals.demo_service.run_in_background') as background:
            forbidden = client.post('/api/evaluations/runs', headers={'Origin': 'https://foreign.example'})
            self.assertEqual(forbidden.status_code, 403)
            background.assert_not_called()
            started = client.post('/api/evaluations/runs')
            self.assertEqual(started.status_code, 202)
            background.assert_called_once()
            id = started.json()['id']
            self.assertEqual(client.get('/api/evaluations/runs/' + id).json()['status'], 'queued')
            self.assertEqual(client.post('/api/evaluations/runs').status_code, 409)
            self.store.release(id)

    def test_restart_marks_orphaned_runs_without_repeating_paid_calls(self):
        run = self.store.create({})
        self.store.release(run['id'])
        with TestClient(self.app) as client:
            self.assertEqual(client.get('/api/evaluations/runs/' + run['id']).json()['status'], 'interrupted')
