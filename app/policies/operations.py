"""Persisted operations, executed by FastAPI's background worker pool."""
import json
import logging
from pathlib import Path
from uuid import uuid4

from app.policies.store import PolicyConflict

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
logger = logging.getLogger(__name__)


def validate_filename(filename):
    if not filename or len(filename) > 200 or '/' in filename or '\\' in filename or any(ord(c) < 32 for c in filename):
        raise ValueError('Use a filename without folders or control characters, at most 200 characters.')
    if Path(filename).suffix.lower() not in {'.pdf', '.html', '.htm', '.txt'}:
        raise ValueError('Upload a PDF, HTML or UTF-8 text file.')


class PolicyOperations:
    def __init__(self, library):
        self.library = library
        self.store = library.store

    def save(self, operation):
        with self.store.connect() as db:
            db.execute('INSERT OR REPLACE INTO operations VALUES (?,?)', (operation['id'], json.dumps(operation)))

    def get(self, operation_id):
        with self.store.connect() as db:
            row = db.execute('SELECT payload FROM operations WHERE id=?', (operation_id,)).fetchone()
        if not row:
            raise KeyError('Operation not found')
        return json.loads(row[0])

    def start(self, policy, kind='upload', preview_id=None):
        operation = {'id': uuid4().hex, 'policy_id': policy['id'], 'kind': kind,
                     'version': policy['version'], 'preview_id': preview_id,
                     'status': 'queued', 'stage': 'Waiting to process', 'error': None}
        self.save(operation)
        return operation

    def upload(self, filename, content):
        validate_filename(filename)
        if not content or len(content) > MAX_UPLOAD_BYTES:
            raise ValueError('Upload a non-empty file of at most 20 MiB.')
        with self.store.lock:
            if any(p['filename'].casefold() == filename.casefold() for p in self.store.list()):
                raise PolicyConflict('A policy with that filename already exists. Rename the file before uploading.')
            policy = self.store.create(filename, content)
            policy['status'] = 'processing'
            self.store.save(policy)
            return self.start(policy)

    def run(self, operation_id):
        with self.store.lock:
            operation = self.get(operation_id)
            if operation['status'] != 'queued':
                return
            try:
                policy = self.store.checked(operation['policy_id'], operation['version'])
                operation.update(status='running', stage='Extracting and chunking')
                self.save(operation)
                self.library.reindex(policy['id'])
                operation.update(status='succeeded', stage='Ready for questions')
            except Exception as exc:
                logger.warning('Policy operation failed (%s)', type(exc).__name__)
                operation.update(status='failed', stage='Processing failed', error=(str(exc) if isinstance(exc, ValueError) else 'Processing could not finish. Retry or upload a readable policy.'))
                try:
                    policy = self.store.get(operation['policy_id'])
                    policy['status'] = 'ready' if policy['revision'] else 'failed'
                    self.store.save(policy)
                except KeyError:
                    pass
            self.save(operation)

    def recover(self):
        with self.store.connect() as db:
            operations = [json.loads(row[0]) for row in db.execute('SELECT payload FROM operations')]
        for operation in operations:
            if operation['status'] in {'queued', 'running'}:
                operation.update(status='failed', stage='Processing interrupted', error='The server restarted. Retry processing.')
                self.save(operation)
                try:
                    policy = self.store.get(operation['policy_id'])
                    policy['status'] = 'ready' if policy['revision'] else 'failed'
                    self.store.save(policy)
                except KeyError:
                    pass
