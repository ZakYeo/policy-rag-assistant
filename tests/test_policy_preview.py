import unittest
from tests import test_policy_upload
from unittest.mock import patch
from app.policies.preview import PolicyPreviews
from app.policies.store import PolicyConflict


class PreviewTests(unittest.TestCase):
    def setUp(self):
        test_policy_upload.UploadTests.setUp(self)
        operation = self.operations.upload('travel.txt', ('Keep receipts. Manager approval is required.\n\n' * 30).encode())
        self.operations.run(operation['id'])
        self.policy = self.library.store.get(operation['policy_id'])
        self.previews = PolicyPreviews(self.library)
        self.settings = {**self.policy['settings'], 'strategy': 'sentences', 'size': 150, 'overlap': 10}

    def test_preview_does_not_change_search_and_apply_activates_exact_preview(self):
        preview = self.previews.create(self.policy['id'], self.settings, self.policy['version'])
        self.assertEqual(self.library.store.get(self.policy['id'])['revision'], self.policy['revision'])
        operation = self.previews.apply(self.policy['id'], preview['id'], self.policy['version'])
        self.operations.run(operation['id'])
        policy = self.library.store.get(self.policy['id'])
        self.assertEqual(policy['revision'], preview['id'])
        self.assertEqual(policy['settings'], self.settings)
        self.assertEqual(self.library.store.revision(policy['revision'])['chunks'], preview['chunks'])

    def test_stale_preview_is_rejected_after_rename(self):
        preview = self.previews.create(self.policy['id'], self.settings, self.policy['version'])
        self.library.store.rename(self.policy['id'], 'Changed title', self.policy['version'])
        with self.assertRaises(PolicyConflict):
            self.previews.apply(self.policy['id'], preview['id'], self.policy['version'] + 1)

    def test_failed_apply_and_restart_keep_old_revision_searchable(self):
        preview = self.previews.create(self.policy['id'], self.settings, self.policy['version'])
        operation = self.previews.apply(self.policy['id'], preview['id'], self.policy['version'])
        with patch.object(self.library.indexer, 'upsert_chunks', side_effect=RuntimeError('failure')):
            self.operations.run(operation['id'])
        self.assertEqual(self.operations.get(operation['id'])['status'], 'failed')
        self.assertEqual(self.library.store.get(self.policy['id'])['revision'], self.policy['revision'])
        operation = self.previews.apply(self.policy['id'], preview['id'], self.policy['version'])
        self.operations.recover()
        self.assertEqual(self.operations.get(operation['id'])['status'], 'failed')
        self.assertEqual(self.library.store.get(self.policy['id'])['revision'], self.policy['revision'])
