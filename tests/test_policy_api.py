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

    def test_rename_updates_catalogue_but_keeps_identity_and_rejects_stale_edit(self):
        policy = self.library.store.list()[0]
        url = f"/api/policies/{policy['id']}"
        response = self.client.patch(url, json={'title': 'New policy title', 'version': policy['version']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['filename'], policy['filename'])
        with self.library.snapshot() as (documents, _):
            self.assertEqual(documents[0].title, 'New policy title')
        self.assertEqual(self.client.patch(url, json={'title': 'Stale', 'version': 1}).status_code, 409)
        self.assertEqual(self.client.patch(url, json={'title': '   ', 'version': 2}).status_code, 400)
        self.assertEqual(self.client.patch(url, json={'title': 'Foreign', 'version': 2}, headers={'Origin': 'https://foreign.example'}).status_code, 403)

    def test_upload_download_and_delete_are_connected_to_active_library(self):
        response = self.client.post('/api/policies', content=b'Keep travel receipts for reimbursement.', headers={'X-Filename': 'travel.txt'})
        self.assertEqual(response.status_code, 202)
        operation = self.client.get('/api/operations/' + response.json()['id']).json()
        self.assertEqual(operation['status'], 'succeeded')
        url = '/api/policies/' + operation['policy_id']
        policy = self.client.get(url).json()
        self.assertEqual(policy['content'][0]['location'], 'Text')
        original = self.client.get(url + '/original')
        self.assertEqual(original.content, b'Keep travel receipts for reimbursement.')
        self.assertIn('attachment', original.headers['content-disposition'])
        self.assertEqual(self.client.request('DELETE', url, json={'version': policy['version']}).status_code, 200)
        self.assertEqual(self.client.get(url).status_code, 404)
