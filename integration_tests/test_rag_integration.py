from __future__ import annotations

import unittest
from pathlib import Path

from app.evals.harness import RagIntegrationHarness


class RagIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.harness = RagIntegrationHarness(Path("documents"))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.harness.close()

    def test_pipeline_creates_isolated_artifacts(self) -> None:
        self.assertTrue(self.harness.extracted_output.exists())
        self.assertTrue(self.harness.chunk_output.exists())
        self.assertTrue(self.harness.vector_store_dir.exists())
        self.assertEqual(len(self.harness.documents), 3)
        self.assertGreaterEqual(len(self.harness.chunks), 10)
        self.assertEqual(self.harness.indexer.count(), len(self.harness.chunks))

    def test_ai_policy_question_returns_ai_guidance(self) -> None:
        result = self.harness.run_question("Can I put customer data into a public AI tool?")

        self.assertEqual(
            [document["document_name"] for document in result.routed_documents],
            ["northstar-ai-acceptable-use-policy.pdf"],
        )
        self.assertIn("customer data into a public AI tool No Prohibited", result.answer)

    def test_working_hours_question_returns_handbook_guidance(self) -> None:
        result = self.harness.run_question("What are the core working hours?")

        self.assertEqual(
            [document["document_name"] for document in result.routed_documents],
            ["northstar-employee-handbook.pdf"],
        )
        self.assertIn("between 10:00 and 16:00", result.answer)

    def test_lost_laptop_question_routes_to_security_policy(self) -> None:
        result = self.harness.run_question("How do I report a lost company laptop?")

        self.assertIn(
            "northstar-information-security-policy.pdf",
            [document["document_name"] for document in result.routed_documents],
        )
        combined_text = " ".join(chunk["text"] for chunk in result.retrieved_chunks)
        self.assertIn("Lost company laptop Immediately", combined_text)
        self.assertIn("Security hotline or incident channel", combined_text)

    def test_password_question_returns_security_guidance(self) -> None:
        result = self.harness.run_question("Can I share passwords?")

        self.assertEqual(
            [document["document_name"] for document in result.routed_documents],
            ["northstar-information-security-policy.pdf"],
        )
        self.assertIn("keep passwords secret", result.answer)
        self.assertIn("Do not share accounts, tokens, or MFA codes", result.answer)

    def test_remote_work_question_returns_handbook_guidance(self) -> None:
        result = self.harness.run_question("Is remote work allowed?")

        self.assertEqual(
            [document["document_name"] for document in result.routed_documents],
            ["northstar-employee-handbook.pdf"],
        )
        self.assertIn("Remote work is allowed only", result.answer)


if __name__ == "__main__":
    unittest.main()
