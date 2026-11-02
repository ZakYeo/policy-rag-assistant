from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, replace
from functools import lru_cache
import logging
from pathlib import Path
from uuid import uuid4

from app.config import get_settings
from app.ingest.chunker import chunk_documents
from app.ingest.extractor import extract_document
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
            self.store.import_existing(self.documents_dir)
            for policy in self.store.list():
                if not policy['revision'] and policy['status'] == 'pending':
                    self.reindex(policy['id'])

    def reindex(self, policy_id):
        with self.store.lock:
            policy = self.store.get(policy_id)
            document = extract_document(self.store.original(policy_id))
            document = replace(document, document_id=policy_id, document_name=policy['filename'])
            revision_id = uuid4().hex
            chunks = [replace(chunk, chunk_id=f'{revision_id}:{chunk.chunk_id}', revision=revision_id)
                      for chunk in chunk_documents([document], policy['settings']['size'], policy['settings']['overlap'])]
            if not chunks:
                raise ValueError('The policy contains no readable text.')
            revision = {'id': revision_id, 'policy_id': policy_id,
                        'content': [asdict(page) for page in document.pages],
                        'settings': policy['settings'], 'chunks': [asdict(chunk) for chunk in chunks]}
            self.store.save_revision(revision)
            self.indexer.upsert_chunks(chunks)
            policy.update(revision=revision_id, chunk_count=len(chunks), status='ready')
            self.store.save(policy)
            return policy

    def delete(self, policy_id, version):
        with self.store.lock:
            policy = self.store.checked(policy_id, version)
            source = self.store.original(policy_id)
            self.store.remove(policy_id)
            # Deactivation happens first; cleanup cannot restore searchable content.
            try:
                self.indexer.delete_document(policy_id)
                source.unlink(missing_ok=True)
                with self.store.connect() as db:
                    for revision_id, payload in db.execute('SELECT id, payload FROM revisions').fetchall():
                        import json
                        if json.loads(payload)['policy_id'] == policy['id']:
                            db.execute('DELETE FROM revisions WHERE id=?', (revision_id,))
            except Exception:
                logging.getLogger(__name__).exception('Deleted policy cleanup will be retried at startup')

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


@lru_cache
def get_library():
    settings = get_settings()
    library = PolicyLibrary(settings.vector_store_dir.parent / 'policies', settings.documents_dir,
                            build_default_embedder())
    library.initialize()
    return library
