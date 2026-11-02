import tempfile
import unittest
from pathlib import Path

from app.policies.store import PolicyStore, PolicyConflict


class PolicyStoreTests(unittest.TestCase):
    def test_import_is_idempotent_and_preserves_original_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            store = PolicyStore(Path(directory))
            store.import_existing(Path('documents'))
            first = store.list()
            store.import_existing(Path('documents'))
            self.assertEqual(first, store.list())
            self.assertEqual(len(first), 3)
            policy = store.get('northstar-employee-handbook')
            self.assertEqual(policy['title'], 'Employee Handbook')
            self.assertTrue(store.original(policy['id']).is_file())
            self.assertEqual(policy['settings']['size'], 900)

    def test_rename_is_versioned_and_does_not_change_original(self):
        with tempfile.TemporaryDirectory() as directory:
            store = PolicyStore(Path(directory))
            store.import_existing(Path('documents'))
            policy = store.get('northstar-employee-handbook')
            renamed = store.rename(policy['id'], 'People handbook', policy['version'])
            self.assertEqual(renamed['title'], 'People handbook')
            self.assertEqual(renamed['filename'], policy['filename'])
            with self.assertRaises(PolicyConflict):
                store.rename(policy['id'], 'Stale edit', policy['version'])
            self.assertEqual(PolicyStore(Path(directory)).get(policy['id']), renamed)
