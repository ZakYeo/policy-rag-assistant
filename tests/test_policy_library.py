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

    def test_cli_import_refreshes_original_and_uses_shared_active_revision(self):
        from app.policies.import_cli import import_directory
        with tempfile.TemporaryDirectory() as directory:
            library = self.library(directory)
            library.initialize()
            policy = library.store.list()[0]
            previous_revision = policy['revision']
            import_directory(library, Path('documents'), 300, 30)
            policy = library.store.get(policy['id'])
            self.assertNotEqual(policy['revision'], previous_revision)
            self.assertEqual(policy['settings']['size'], 300)
            self.assertEqual(len(library.store.list()), 3)

    def test_empty_library_answers_without_routing_or_constructing_provider(self):
        from app.assistant import AssistantService
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as directory:
            library = PolicyLibrary(Path(directory), Path(directory) / 'empty', LocalHashEmbedder())
            library.initialize()
            router = Mock()
            with patch('app.assistant.build_default_answerer', side_effect=AssertionError('No provider needed')):
                response = AssistantService(library=library, router=router).answer_question('What are the rules?', answer_provider='openai')
            router.route.assert_not_called()
            self.assertFalse(response.sources)
