import os
import unittest

from fastapi import HTTPException
from app.assistant import AssistantService
from app.config import get_settings
from app.main import create_app
from app.retrieval.answerer import AnswerProviderError
from fastapi.responses import HTMLResponse

from app.web.routes import ask_question, root, status
from app.web.schemas import AskRequest


class FakeAssistantService(AssistantService):
    def __init__(self) -> None:
        pass

    def answer_question(
        self,
        question: str,
        top_k: int | None = None,
        answer_provider: str | None = None,
    ):
        return type(
            "AssistantResponse",
            (),
            {
                "answer": "Mock answer",
                "answer_provider": answer_provider or "extractive",
                "routed_documents": [
                    {
                        "document_id": "northstar-ai-acceptable-use-policy",
                        "document_name": "northstar-ai-acceptable-use-policy.pdf",
                        "title": "AI Acceptable Use Policy",
                    }
                ],
                "routing_provider": "heuristic",
                "routing_rationale": "AI keyword match",
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


class ErrorAssistantService(AssistantService):
    def __init__(self) -> None:
        pass

    def answer_question(
        self,
        question: str,
        top_k: int | None = None,
        answer_provider: str | None = None,
    ):
        raise AnswerProviderError(
            "OpenAI answering is selected but OPENAI_API_KEY is not configured on the backend."
        )


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
        self.assertIn("Answer mode", body)
        self.assertIn('option value="openai" selected', body)

    def test_status_returns_setup_paths(self) -> None:
        payload = status()

        self.assertEqual(payload["name"], "Policy RAG Assistant")
        self.assertEqual(payload["status"], "ready")
        self.assertTrue(payload["documents_dir"].endswith("documents"))
        self.assertTrue(payload["vector_store_dir"].endswith("data/chroma"))

    def test_ask_endpoint_returns_answer_payload(self) -> None:
        response = ask_question(
            AskRequest(question="What is the rule?", answer_provider="openai"),
            assistant=FakeAssistantService(),
        )

        self.assertEqual(response.answer, "Mock answer")
        self.assertEqual(response.answer_provider, "openai")
        self.assertEqual(response.routing_provider, "heuristic")
        self.assertEqual(response.routed_documents[0].document_id, "northstar-ai-acceptable-use-policy")
        self.assertEqual(response.sources[0].document_name, "policy.pdf")
        self.assertEqual(response.retrieved_chunks[0].chunk_id, "chunk-1")

    def test_ask_endpoint_returns_provider_error(self) -> None:
        with self.assertRaises(HTTPException) as exc_info:
            ask_question(
                AskRequest(question="What is the rule?", answer_provider="openai"),
                assistant=ErrorAssistantService(),
            )
        self.assertEqual(exc_info.exception.status_code, 503)
        self.assertIn("OPENAI_API_KEY", exc_info.exception.detail)
