import math
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.retrieval.embeddings import OpenAIEmbedder


class EmbeddingLimitTests(unittest.TestCase):
    def test_long_unicode_inputs_are_bounded_and_return_one_vector_per_chunk(self):
        embedder = OpenAIEmbedder.__new__(OpenAIEmbedder)
        embedder._model = 'text-embedding-3-small'
        calls = []

        def create(*, model, input):
            calls.append(input)
            self.assertLessEqual(sum(len(text.encode('utf-8')) for text in input), 200_000)
            self.assertLessEqual(len(input), 128)
            self.assertTrue(all(0 < len(text.encode('utf-8')) <= 8000 for text in input))
            return SimpleNamespace(data=[SimpleNamespace(index=index, embedding=[1.0, 2.0]) for index in reversed(range(len(input)))])

        embedder._client = SimpleNamespace(embeddings=SimpleNamespace(create=Mock(side_effect=create)))
        originals = ['安全🙂' * 6000, 'a ' * 10000] * 20
        vectors = embedder.embed_texts(originals)
        self.assertEqual(len(vectors), len(originals))
        self.assertGreater(len(calls), 1)
        for vector in vectors:
            self.assertAlmostEqual(math.sqrt(sum(value * value for value in vector)), 1.0)
        self.assertEqual(''.join(piece for call in calls for piece in call), ''.join(originals))
