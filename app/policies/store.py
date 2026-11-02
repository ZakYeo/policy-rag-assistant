from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from uuid import uuid4

from app.retrieval.catalog import POLICY_DOCUMENTS

DEFAULT_SETTINGS = {"strategy": "characters", "size": 900, "overlap": 150, "heading_depth": 2}


class PolicyConflict(ValueError):
    pass


class PolicyStore:
    """Single-instance registry. SQLite commits publish complete immutable revisions."""

    def __init__(self, directory: Path):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.database = directory / "policies.sqlite3"
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS policies (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS revisions (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS operations (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            ''')

    def connect(self):
        return sqlite3.connect(self.database, timeout=30)

    def list(self):
        with self.lock, self.connect() as db:
            return [json.loads(row[0]) for row in db.execute("SELECT payload FROM policies ORDER BY id")]

    def get(self, policy_id: str):
        with self.lock, self.connect() as db:
            row = db.execute("SELECT payload FROM policies WHERE id=?", (policy_id,)).fetchone()
        if row is None:
            raise KeyError("Policy not found")
        return json.loads(row[0])

    def save(self, policy):
        with self.lock, self.connect() as db:
            db.execute("INSERT OR REPLACE INTO policies VALUES (?,?)", (policy['id'], json.dumps(policy)))

    def save_with_operation(self, policy, operation):
        with self.lock, self.connect() as db:
            db.execute('INSERT OR REPLACE INTO policies VALUES (?,?)', (policy['id'], json.dumps(policy)))
            db.execute('INSERT OR REPLACE INTO operations VALUES (?,?)', (operation['id'], json.dumps(operation)))

    def original(self, policy_id):
        return self.directory / self.get(policy_id)['file']

    def import_existing(self, documents_dir: Path):
        with self.lock, self.connect() as db:
            if db.execute("SELECT value FROM metadata WHERE key='imported'").fetchone():
                return
            titles = {doc.document_id: doc.title for doc in POLICY_DOCUMENTS}
            for path in sorted(documents_dir.glob('*.pdf')):
                policy = self.create(path.name, path.read_bytes(), path.stem, titles.get(path.stem))
                db.execute("INSERT OR IGNORE INTO policies VALUES (?,?)", (policy['id'], json.dumps(policy)))
            db.execute("INSERT INTO metadata VALUES ('imported','1')")

    def create(self, filename, content, policy_id=None, title=None):
        policy_id = policy_id or uuid4().hex
        file = f"originals/{uuid4().hex}{Path(filename).suffix.lower()}"
        destination = self.directory / file
        destination.parent.mkdir(exist_ok=True)
        destination.write_bytes(content)
        return {
            'id': policy_id, 'title': title or Path(filename).stem.replace('-', ' '),
            'filename': filename, 'format': Path(filename).suffix.lower().lstrip('.'),
            'file': file, 'version': 1, 'revision': None, 'settings': dict(DEFAULT_SETTINGS),
            'chunk_count': 0, 'status': 'pending',
        }

    def rename(self, policy_id, title, version):
        title = title.strip()
        if not title or len(title) > 160 or any(ord(char) < 32 for char in title):
            raise ValueError('Use a title of 1–160 characters without control characters.')
        with self.lock:
            policy = self.checked(policy_id, version)
            policy.update(title=title, version=version + 1)
            self.save(policy)
            return policy

    def checked(self, policy_id, version):
        policy = self.get(policy_id)
        if policy['version'] != version:
            raise PolicyConflict('This policy has changed. Refresh it and try again.')
        return policy

    def revision(self, revision_id):
        with self.connect() as db:
            row = db.execute("SELECT payload FROM revisions WHERE id=?", (revision_id,)).fetchone()
        if row is None:
            raise KeyError('Revision not found')
        return json.loads(row[0])

    def save_revision(self, revision):
        with self.connect() as db:
            db.execute("INSERT INTO revisions VALUES (?,?)", (revision['id'], json.dumps(revision)))

    def remove(self, policy_id):
        with self.connect() as db:
            db.execute("DELETE FROM policies WHERE id=?", (policy_id,))
