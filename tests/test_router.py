import os
import unittest

from app.config import get_settings
from app.retrieval.catalog import POLICY_DOCUMENTS
from app.retrieval.router import HeuristicDocumentRouter, build_default_router


class RouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)
        get_settings.cache_clear()

    def test_heuristic_router_picks_ai_policy(self) -> None:
        router = HeuristicDocumentRouter()

        result = router.route("Can I paste customer data into a public AI tool?", POLICY_DOCUMENTS)

        self.assertIn("northstar-ai-acceptable-use-policy", result.document_ids)

    def test_heuristic_router_picks_security_policy(self) -> None:
        router = HeuristicDocumentRouter()

        result = router.route("How do I report a security incident or lost device?", POLICY_DOCUMENTS)

        self.assertIn("northstar-information-security-policy", result.document_ids)

    def test_heuristic_router_picks_security_policy_for_lost_laptop(self) -> None:
        router = HeuristicDocumentRouter()

        result = router.route("How do I report a lost company laptop?", POLICY_DOCUMENTS)

        self.assertIn("northstar-information-security-policy", result.document_ids)

    def test_build_default_router_falls_back_to_heuristic_without_key(self) -> None:
        os.environ["ROUTER_PROVIDER"] = "openai"
        os.environ["OPENAI_API_KEY"] = ""
        get_settings.cache_clear()

        router = build_default_router()

        self.assertIsInstance(router, HeuristicDocumentRouter)
