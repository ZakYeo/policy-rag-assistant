import tempfile
import unittest
from pathlib import Path

from app.policies.library import PolicyLibrary
from app.policies.operations import PolicyOperations
from app.policies.preview import PolicyPreviews
from app.retrieval.embeddings import LocalHashEmbedder


class SourceMappingTests(unittest.TestCase):
    def test_grouped_html_chunks_map_to_saved_canonical_sections(self):
        with tempfile.TemporaryDirectory() as directory:
            library = PolicyLibrary(Path(directory), Path(directory) / 'empty', LocalHashEmbedder())
            library.initialize()
            operations = PolicyOperations(library)
            html = '<h1>Travel</h1><p>Intro.</p><h3>Receipts</h3><p>' + ('Keep receipts. ' * 20) + '</p>'
            operation = operations.upload('travel.html', html.encode())
            operations.run(operation['id'])
            policy = library.store.get(operation['policy_id'])
            settings = {**policy['settings'], 'strategy': 'html', 'size': 100, 'overlap': 0, 'heading_depth': 1}
            preview = PolicyPreviews(library).create(policy['id'], settings, policy['version'])
            sections = {section['section_id']: section for section in preview['content']}
            self.assertEqual(len(sections), 1)
            for chunk in preview['chunks']:
                source = sections[chunk['section_id']]['text']
                self.assertLessEqual(chunk['char_end'], len(source))
                self.assertEqual(chunk['text'], chunk['heading_context'] + source[chunk['char_start']:chunk['char_end']])
                self.assertLessEqual(len(chunk['text']), settings['size'])
