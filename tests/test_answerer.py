import unittest

from app.retrieval.answerer import ExtractiveAnswerer
from app.retrieval.retriever import RetrievedChunk


class AnswererTests(unittest.TestCase):
    def test_answer_returns_grounded_extract(self) -> None:
        answerer = ExtractiveAnswerer()
        chunks = [
            RetrievedChunk(
                chunk_id="ai-1",
                document_id="northstar-ai-acceptable-use-policy",
                document_name="northstar-ai-acceptable-use-policy.pdf",
                source_path="documents/northstar-ai-acceptable-use-policy.pdf",
                page_number=1,
                chunk_index=0,
                char_start=0,
                char_end=120,
                text=(
                    "Pasting customer data into a public AI tool No Prohibited. "
                    "Human review is required for high-risk decisions."
                ),
                distance=0.1,
            )
        ]

        result = answerer.answer("Can I put customer data into a public AI tool?", chunks)

        self.assertIn("customer data", result.answer.lower())
        self.assertIn("No Prohibited", result.answer)
        self.assertIn("northstar-ai-acceptable-use-policy.pdf p.1", result.answer)
        self.assertEqual(result.provider, "extractive")

    def test_answer_handles_missing_context(self) -> None:
        answerer = ExtractiveAnswerer()

        result = answerer.answer("What is the policy?", [])

        self.assertIn("could not find supporting policy context", result.answer.lower())
        self.assertEqual(result.sources, [])

    def test_answer_returns_sources(self) -> None:
        answerer = ExtractiveAnswerer()
        chunks = [
            RetrievedChunk(
                chunk_id="security-1",
                document_id="northstar-information-security-policy",
                document_name="northstar-information-security-policy.pdf",
                source_path="documents/northstar-information-security-policy.pdf",
                page_number=2,
                chunk_index=1,
                char_start=100,
                char_end=240,
                text="Restricted information must not be copied to personal storage.",
                distance=0.2,
            )
        ]

        result = answerer.answer("Can I copy restricted information to personal storage?", chunks)

        self.assertEqual(len(result.sources), 1)
        self.assertEqual(result.sources[0].document_name, "northstar-information-security-policy.pdf")
        self.assertEqual(result.sources[0].page_number, 2)
