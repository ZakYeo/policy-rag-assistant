import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from app.policies.library import PolicyLibrary
from app.policies.operations import PolicyOperations
from app.policies.preview import PolicyPreviews
from app.retrieval.embeddings import LocalHashEmbedder


class PolicyConcurrencyTests(unittest.TestCase):
    def test_old_revision_remains_searchable_while_replacement_is_indexing(self):
        with tempfile.TemporaryDirectory() as directory:
            library = PolicyLibrary(Path(directory), Path(directory) / 'empty', LocalHashEmbedder())
            library.initialize()
            operations = PolicyOperations(library)
            upload = operations.upload('travel.txt', b'Travel receipts are required. ' * 20)
            operations.run(upload['id'])
            policy = library.store.get(upload['policy_id'])
            previews = PolicyPreviews(library)
            preview = previews.create(policy['id'], {**policy['settings'], 'size': 200, 'overlap': 20}, policy['version'])
            operation = previews.apply(policy['id'], preview['id'], policy['version'])
            indexing = threading.Event()
            release = threading.Event()
            searched = threading.Event()
            results = []
            original = library.indexer.upsert_chunks

            def delayed(chunks):
                indexing.set()
                release.wait(5)
                return original(chunks)

            def search():
                with library.snapshot() as (documents, retriever):
                    results.extend(retriever.retrieve_filtered('travel receipts', 2, [documents[0].document_id]))
                searched.set()

            with patch.object(library.indexer, 'upsert_chunks', side_effect=delayed):
                worker = threading.Thread(target=operations.run, args=(operation['id'],))
                worker.start()
                self.assertTrue(indexing.wait(3))
                reader = threading.Thread(target=search)
                reader.start()
                try:
                    self.assertTrue(searched.wait(1), 'Old revision retrieval blocked by staging')
                    self.assertTrue(all(chunk.chunk_id.startswith(policy['revision']) for chunk in results))
                finally:
                    release.set()
                    worker.join(5)
                    reader.join(5)
            self.assertEqual(operations.get(operation['id'])['status'], 'succeeded')
