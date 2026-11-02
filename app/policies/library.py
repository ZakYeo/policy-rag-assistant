from __future__ import annotations

from contextlib import contextmanager
import json
from app.ingest.chunker import Chunk
from functools import lru_cache
import logging
import threading
from pathlib import Path

from app.policies.ingestion import build_revision
from app.config import get_settings
from app.ingest.indexer import ChunkIndexer
from app.policies.store import PolicyStore
from app.retrieval.catalog import PolicyDocument
from app.retrieval.embeddings import build_default_embedder
from app.retrieval.retriever import ChunkRetriever


class PolicyLibrary:
    def __init__(self, directory: Path, documents_dir: Path, embedder):
        self.store = PolicyStore(directory)
        self.documents_dir = documents_dir
        self.indexer = ChunkIndexer(directory / 'vectors', 'managed_policies', embedder)
        self.retriever = ChunkRetriever(directory / 'vectors', 'managed_policies', embedder)

    def initialize(self):
        with self.store.lock:
            from app.policies.operations import PolicyOperations
            PolicyOperations(self).recover()
            self.store.import_existing(self.documents_dir)
            for policy in self.store.list():
                if not policy['revision'] and policy['status'] == 'pending':
                    self.reindex(policy['id'])
            self.cleanup()

    def reindex(self, policy_id):
        with self.store.lock:
            policy = self.store.get(policy_id)
            revision = build_revision(self.store, policy)
            self.store.save_revision(revision)
            return self.activate(revision, policy['version'])

    def activate(self, revision, version):
        with self.store.lock:
            policy = self.store.checked(revision['policy_id'], version)
            chunks = [Chunk(**chunk) for chunk in revision['chunks']]
            self.indexer.upsert_chunks(chunks)
            policy.update(revision=revision['id'], chunk_count=len(chunks), status='ready',
                          settings=revision['settings'], version=version + bool(policy['revision']))
            self.store.save(policy)
            self.cleanup()
            return policy

    def delete(self, policy_id, version):
        with self.store.lock:
            self.store.checked(policy_id, version)
            self.store.remove(policy_id)
            self.cleanup()

    def cleanup(self):
        # Always publish/deactivate before cleanup. Failed cleanup is safe to retry.
        try:
            policies = self.store.list()
            self.indexer.prune_revisions({p['revision'] for p in policies if p['revision']})
            originals = {p['file'] for p in policies}
            for path in (self.store.directory / 'originals').glob('*'):
                if str(path.relative_to(self.store.directory)) not in originals:
                    path.unlink(missing_ok=True)
            active_ids = {p['id'] for p in policies}
            with self.store.connect() as db:
                for revision_id, payload in db.execute('SELECT id, payload FROM revisions').fetchall():
                    if json.loads(payload)['policy_id'] not in active_ids:
                        db.execute('DELETE FROM revisions WHERE id=?', (revision_id,))
        except Exception:
            logging.getLogger(__name__).exception('Policy cleanup will be retried at startup')

    @contextmanager
    def snapshot(self):
        # Routing/retrieval hold a consistent catalogue; generation releases the lock.
        with self.store.lock:
            policies = [p for p in self.store.list() if p['revision']]
            documents = [PolicyDocument(p['id'], p['filename'], p['title'],
                         ' '.join(page['text'] for page in self.store.revision(p['revision'])['content'])[:2000])
                         for p in policies]
            yield documents, RevisionRetriever(self.retriever, [p['revision'] for p in policies])


class RevisionRetriever:
    def __init__(self, retriever, revisions):
        self.retriever, self.revisions = retriever, revisions

    def retrieve_filtered(self, query, top_k, document_ids):
        if not self.revisions or not document_ids:
            return []
        return self.retriever.retrieve_filtered(query, top_k, document_ids, self.revisions)


_initialization_lock = threading.Lock()


def get_library():
    with _initialization_lock:
        return _cached_library()


@lru_cache
def _cached_library():
    settings = get_settings()
    library = PolicyLibrary(settings.vector_store_dir.parent / 'policies', settings.documents_dir,
                            build_default_embedder())
    library.initialize()
    return library
