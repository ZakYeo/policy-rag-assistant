import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.policies.library import PolicyLibrary
from app.retrieval.embeddings import LocalHashEmbedder


class PolicyLibraryTests(unittest.TestCase):
    def library(self, directory):
        return PolicyLibrary(Path(directory), Path('documents'), LocalHashEmbedder())

    def test_bootstrap_is_searchable_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            library = self.library(directory)
            library.initialize()
            with library.snapshot() as (documents, retriever):
                self.assertEqual(len(documents), 3)
                chunks = retriever.retrieve_filtered('customer data public AI', 4, [documents[0].document_id])
                self.assertTrue(chunks)
            revisions = [p['revision'] for p in library.store.list()]
            library.initialize()
            self.assertEqual(revisions, [p['revision'] for p in library.store.list()])

    def test_failed_indexing_does_not_activate_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            library = self.library(directory)
            library.initialize()
            policy = library.store.list()[0]
            original = policy['revision']
            with patch.object(library.indexer, 'upsert_chunks', side_effect=RuntimeError('failure')):
                with self.assertRaises(RuntimeError):
                    library.reindex(policy['id'])
            self.assertEqual(library.store.get(policy['id'])['revision'], original)

    def test_delete_deactivates_policy_and_removes_stored_source_and_vectors(self):
        with tempfile.TemporaryDirectory() as directory:
            library = self.library(directory)
            library.initialize()
            policy = library.store.list()[0]
            source = library.store.original(policy['id'])
            library.delete(policy['id'], policy['version'])
            self.assertFalse(source.exists())
            with library.snapshot() as (documents, retriever):
                self.assertNotIn(policy['id'], [doc.document_id for doc in documents])
                self.assertEqual(retriever.retrieve_filtered('AI', 4, [policy['id']]), [])
            library.initialize()
            self.assertEqual(len(library.store.list()), 2)
