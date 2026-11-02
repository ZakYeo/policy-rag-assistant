import unittest

from app.policies.strategies import split_section, validate_settings, strategy_sections


class StrategyTests(unittest.TestCase):
    def settings(self, strategy, size=100, overlap=0):
        return {'strategy': strategy, 'size': size, 'overlap': overlap, 'heading_depth': 2}

    def test_sentence_chunks_end_at_sentence_boundaries_and_keep_offsets(self):
        text = 'First sentence has useful content. Second sentence also has useful content. Third sentence ends here.'
        chunks = split_section(text, self.settings('sentences'))
        self.assertEqual(len(chunks), 2)
        self.assertTrue(chunks[0][2].endswith('.'))
        for start, end, chunk in chunks:
            self.assertEqual(chunk, text[start:end])

    def test_paragraphs_keep_boundaries_and_split_oversized_units(self):
        text = ('A' * 70) + '\n\n' + ('B' * 70) + '\n\n' + ('C' * 250)
        chunks = split_section(text, self.settings('paragraphs'))
        self.assertEqual(chunks[0][2], 'A' * 70)
        self.assertTrue(all(len(chunk) <= 100 for _, _, chunk in chunks))
        self.assertEqual(''.join(chunk for _, _, chunk in chunks).replace('\n', ''), text.replace('\n', ''))

    def test_overlap_unicode_and_large_character_settings_are_bounded(self):
        text = ('Résumé. 安全 policies apply. ' * 30).strip()
        chunks = split_section(text, self.settings('sentences', overlap=20))
        self.assertGreater(len(chunks), 2)
        self.assertTrue(all(len(chunk) <= 100 for _, _, chunk in chunks))
        self.assertTrue(chunks[1][2].startswith(chunks[0][2][-20:].lstrip()))
        for start, end, chunk in chunks:
            self.assertEqual(chunk, text[start:end])

    def test_html_heading_depth_groups_subsections(self):
        sections = [{'text': 'Travel\n\nIntro', 'heading': 'Travel', 'level': 1, 'location': 'Travel', 'page_number': 1},
                    {'text': 'Receipts\n\nKeep them', 'heading': 'Receipts', 'level': 3, 'location': 'Receipts', 'page_number': 1},
                    {'text': 'Meals\n\nLimit applies', 'heading': 'Meals', 'level': 2, 'location': 'Meals', 'page_number': 1}]
        grouped = strategy_sections(sections, self.settings('html'))
        self.assertEqual(len(grouped), 2)
        self.assertIn('Receipts', grouped[0]['text'])

    def test_settings_reject_invalid_values_and_html_for_non_html_files(self):
        for settings in [self.settings('unknown'), self.settings('characters', 10), self.settings('characters', overlap=100)]:
            with self.assertRaises(ValueError):
                validate_settings(settings, 'pdf')
        with self.assertRaises(ValueError):
            validate_settings(self.settings('html'), 'pdf')
