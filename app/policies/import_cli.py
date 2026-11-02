"""Synchronise CLI PDF ingestion with the policy-management catalogue."""
from app.policies.ingestion import build_revision
from app.policies.store import DEFAULT_SETTINGS


def import_directory(library, directory, size=900, overlap=150):
    count = 0
    with library.store.lock:
        existing = {policy['filename']: policy for policy in library.store.list()}
        for path in sorted(directory.glob('*.pdf')):
            previous = existing.get(path.name)
            candidate = library.store.create(path.name, path.read_bytes(),
                                             previous['id'] if previous else path.stem,
                                             previous['title'] if previous else None)
            if previous:
                candidate = {**previous, 'file': candidate['file']}
            settings = {**DEFAULT_SETTINGS, 'size': size, 'overlap': overlap}
            revision = build_revision(library.store, candidate, settings)
            library.store.save_revision(revision)
            # Stage embeddings before changing the catalogue or original-file pointer.
            library.stage_revision(revision)
            library.publish_revision(revision, candidate)
            count += len(revision['chunks'])
    return count
