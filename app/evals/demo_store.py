"""Local persisted runs. A database constraint enforces one active evaluation."""
import json
import sqlite3
import fcntl
from datetime import datetime, timezone
from uuid import uuid4


def now():
    return datetime.now(timezone.utc).isoformat()


class RunConflict(ValueError):
    pass


class RunStore:
    def __init__(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / 'evaluations.sqlite3'
        self.lease_path = directory / 'evaluation.lock'
        self._leases = {}
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, status TEXT NOT NULL, payload TEXT NOT NULL)')
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_active_run ON runs ((1)) WHERE status IN ('queued', 'running')")

    def connect(self):
        return sqlite3.connect(self.path, timeout=30)

    def create(self, metadata):
        lease = self._acquire()
        run = {**metadata, 'id': uuid4().hex, 'status': 'queued', 'created_at': now(),
               'finished_at': None, 'progress': 0, 'total': metadata.get('total', 5), 'stage': 'Queued',
               'rows': [], 'summary': {}, 'error': None}
        try:
            with self.connect() as db:
                db.execute('INSERT INTO runs VALUES (?, ?, ?)', (run['id'], run['status'], json.dumps(run, allow_nan=False)))
        except sqlite3.IntegrityError as exc:
            lease.close()
            raise RunConflict('An evaluation is already running.') from exc
        except BaseException:
            lease.close()
            raise
        self._leases[run['id']] = lease
        return run

    def _acquire(self):
        lease = self.lease_path.open('a')
        try:
            fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            lease.close()
            raise RunConflict('An evaluation is already running.') from exc
        return lease

    def release(self, id):
        lease = self._leases.pop(id, None)
        if lease:
            lease.close()

    def save(self, run):
        with self.connect() as db:
            db.execute('UPDATE runs SET status=?, payload=? WHERE id=?', (run['status'], json.dumps(run, allow_nan=False), run['id']))
        if run['status'] not in {'queued', 'running'}:
            self.release(run['id'])

    def get(self, id):
        with self.connect() as db:
            row = db.execute('SELECT payload FROM runs WHERE id=?', (id,)).fetchone()
        if row is None:
            raise KeyError('Evaluation not found')
        return json.loads(row[0])

    def list(self):
        with self.connect() as db:
            rows = db.execute('SELECT payload FROM runs ORDER BY rowid DESC LIMIT 50').fetchall()
        return [{k: v for k, v in json.loads(row[0]).items() if k not in {'rows', 'policy_fingerprint', 'definitions'}} for row in rows]

    def recover(self):
        try:
            lease = self._acquire()
        except RunConflict:
            return  # Another live process owns this run, including an explicit CLI run.
        with lease, self.connect() as db:
            rows = db.execute("SELECT payload FROM runs WHERE status IN ('queued','running')").fetchall()
            for row in rows:
                run = json.loads(row[0])
                run.update(status='interrupted', finished_at=now(), stage='Interrupted by server restart',
                           error='Evaluation interrupted. Saved results are retained. Start a new run explicitly to retry.')
                db.execute('UPDATE runs SET status=?, payload=? WHERE id=?', (run['status'], json.dumps(run), run['id']))
