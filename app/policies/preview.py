from app.policies.ingestion import build_revision
from app.policies.operations import PolicyOperations
from app.policies.store import PolicyConflict


class PolicyPreviews:
    def __init__(self, library):
        self.library = library
        self.store = library.store

    def create(self, policy_id, settings, version):
        with self.library.write_lock:
            policy = self.store.checked(policy_id, version)
            if not policy['revision'] or policy['status'] != 'ready':
                raise PolicyConflict('Wait until this policy is ready before changing its chunking.')
            revision = build_revision(self.store, policy, settings)
            self.store.save_revision(revision)
            return revision

    def apply(self, policy_id, preview_id, version):
        with self.library.write_lock:
            policy = self.store.checked(policy_id, version)
            preview = self.store.revision(preview_id)
            if preview['policy_id'] != policy_id or preview['version'] != version or policy['status'] != 'ready':
                raise PolicyConflict('This preview is out of date. Preview the current settings again.')
            policy['status'] = 'processing'
            return PolicyOperations(self.library).start(policy, 'apply', preview_id)
