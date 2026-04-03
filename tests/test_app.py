import os
import unittest

from app.assistant import AssistantService
from app.config import get_settings
from app.main import create_app
from fastapi.responses import HTMLResponse

from app.web.routes import ask_question, root, status
from app.web.schemas import AskRequest


class FakeAssistantService(AssistantService):
    def __init__(self) -> None:
        pass

    def answer_question(self, question: str, top_k: int | None = None):
        return type(
            "AssistantResponse",
            (),
            {
                "answer": "Mock answer",
                "answer_provider": "extractive",
                "sources": [
                    {
                        "document_name": "policy.pdf",
                        "page_number": 1,
                        "chunk_id": "chunk-1",
                    }
                ],
                "retrieved_chunks": [
                    {
                        "chunk_id": "chunk-1",
                        "document_name": "policy.pdf",
                        "page_number": 1,
                        "chunk_index": 0,
                        "distance": 0.1,
                        "text": "policy text",
                    }
                ],
            },
        )()


class AppSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = os.environ.copy()
        os.environ["APP_ENV"] = "test"
        get_settings.cache_clear()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)
        get_settings.cache_clear()

    def test_healthcheck_returns_environment(self) -> None:
        app = create_app()
        health_route = next(route for route in app.routes if route.path == "/health")

        payload = health_route.endpoint()

        self.assertEqual(payload, {"status": "ok", "environment": "test"})

    def test_root_returns_setup_status(self) -> None:
        response = root()

        self.assertIsInstance(response, HTMLResponse)
        body = response.body.decode("utf-8")
        self.assertIn("Policy RAG Assistant", body)
        self.assertIn("Ask Policy Assistant", body)

    def test_status_returns_setup_paths(self) -> None:
        payload = status()

        self.assertEqual(payload["name"], "Policy RAG Assistant")
        self.assertEqual(payload["status"], "ready")
        self.assertTrue(payload["documents_dir"].endswith("documents"))
        self.assertTrue(payload["vector_store_dir"].endswith("data/chroma"))

    def test_ask_endpoint_returns_answer_payload(self) -> None:
        response = ask_question(AskRequest(question="What is the rule?"), assistant=FakeAssistantService())

        self.assertEqual(response.answer, "Mock answer")
        self.assertEqual(response.answer_provider, "extractive")
        self.assertEqual(response.sources[0].document_name, "policy.pdf")
        self.assertEqual(response.retrieved_chunks[0].chunk_id, "chunk-1")
