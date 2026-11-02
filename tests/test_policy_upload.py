import tempfile
import unittest
from pathlib import Path

from app.policies.library import PolicyLibrary
from app.policies.operations import PolicyOperations
from app.retrieval.embeddings import LocalHashEmbedder


class UploadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.library = PolicyLibrary(Path(self.temp.name), Path(self.temp.name) / 'empty', LocalHashEmbedder())
        self.library.initialize()
        self.operations = PolicyOperations(self.library)

    def test_text_upload_becomes_searchable_and_duplicate_is_rejected(self):
        operation = self.operations.upload('travel.txt', b'Travel reimbursement requires receipts. ' * 20)
        self.operations.run(operation['id'])
        policy = self.library.store.get(operation['policy_id'])
        self.assertEqual(policy['status'], 'ready')
        with self.library.snapshot() as (docs, retriever):
            self.assertTrue(retriever.retrieve_filtered('travel receipts', 2, [docs[0].document_id]))
        with self.assertRaises(ValueError):
            self.operations.upload('travel.txt', b'New content')

    def test_bad_document_fails_without_activating_content(self):
        operation = self.operations.upload('invalid.pdf', b'not a pdf')
        self.operations.run(operation['id'])
        self.assertEqual(self.operations.get(operation['id'])['status'], 'failed')
        self.assertIsNone(self.library.store.get(operation['policy_id'])['revision'])

    def test_html_content_is_extracted_without_active_content(self):
        operation = self.operations.upload('travel.html', b'<html><body><h1>Travel</h1><p>Keep receipts.</p><script>stealSecret()</script></body></html>')
        self.operations.run(operation['id'])
        policy = self.library.store.get(operation['policy_id'])
        content = self.library.store.revision(policy['revision'])['content']
        self.assertIn('Keep receipts.', str(content))
        self.assertNotIn('stealSecret', str(content))

    def test_unsafe_filenames_and_binary_text_are_rejected(self):
        for name in ['../test.txt', 'C:\\test.txt', 'test.exe']:
            with self.assertRaises(ValueError):
                self.operations.upload(name, b'text')
        operation = self.operations.upload('binary.txt', b'\x00\x01binary')
        self.operations.run(operation['id'])
        self.assertEqual(self.operations.get(operation['id'])['status'], 'failed')
