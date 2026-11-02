import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from app.main import create_app
from app.policies.library import PolicyLibrary
from app.policies.routes import library_dependency
from app.retrieval.embeddings import LocalHashEmbedder


class PolicyApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.library = PolicyLibrary(Path(self.temp.name), Path('documents'), LocalHashEmbedder())
        self.library.initialize()
        app = create_app()
        app.dependency_overrides[library_dependency] = lambda: self.library
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_list_content_and_chunks_do_not_expose_server_paths(self):
        response = self.client.get('/api/policies')
        self.assertEqual(response.status_code, 200)
        policies = response.json()
        self.assertEqual(len(policies), 3)
        self.assertNotIn('file', policies[0])
        policy_id = policies[0]['id']
        detail = self.client.get(f'/api/policies/{policy_id}').json()
        self.assertTrue(detail['content'])
        chunks = self.client.get(f'/api/policies/{policy_id}/chunks').json()
        self.assertTrue(chunks['items'])
        self.assertNotIn('source_path', chunks['items'][0])
        self.assertEqual(self.client.get('/api/policies/missing').status_code, 404)
