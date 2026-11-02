import json
import unittest
from pathlib import Path

from app.evals.harness import RagIntegrationHarness


ROOT = Path(__file__).resolve().parent.parent


class SampleQuestionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.groups = json.loads((ROOT / "frontend/src/models/sampleQuestions.json").read_text())
        cls.harness = RagIntegrationHarness(ROOT / "documents")

    @classmethod
    def tearDownClass(cls):
        cls.harness.close()

    def test_questions_cover_all_current_policies_with_unique_ids(self):
        questions = [question for group in self.groups for question in group["questions"]]
        self.assertEqual(len(questions), 8)
        self.assertEqual(len({question["id"] for question in questions}), len(questions))
        known_ids = {doc["document_id"] for doc in self.harness.document_catalog}
        declared_ids = {policy for question in questions for policy in question["policyIds"]}
        self.assertEqual(declared_ids, known_ids)

    def test_cross_policy_questions_retrieve_the_declared_documents(self):
        questions = [
            question
            for group in self.groups
            for question in group["questions"]
            if len(question["policyIds"]) > 1
        ]
        self.assertEqual(len(questions), 4)
        for question in questions:
            with self.subTest(question=question["id"]):
                result = self.harness.run_question(question["question"])
                retrieved = {Path(chunk["document_name"]).stem for chunk in result.retrieved_chunks}
                self.assertTrue(set(question["policyIds"]).issubset(retrieved), retrieved)
