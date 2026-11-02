import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.assistant import AssistantService
from app.main import create_app
from app.retrieval.answerer import AnswerResult, AnswerSource, OpenAIAnswerer
from app.retrieval.retriever import RetrievedChunk
from app.retrieval.router import RoutingResult
from app.web.routes import get_assistant_service


CHUNK = RetrievedChunk(
    chunk_id="policy-p1-c0",
    document_id="northstar-ai-acceptable-use-policy",
    document_name="northstar-ai-acceptable-use-policy.pdf",
    source_path="documents/policy.pdf",
    page_number=1,
    chunk_index=0,
    char_start=0,
    char_end=30,
    text="Do not share customer data.",
    distance=0.1,
)
SOURCE = AnswerSource(CHUNK.document_name, 1, CHUNK.chunk_id)


class FakeAnswerer:
    closed = False

    def answer(self, question, chunks):
        return AnswerResult("Do not share.", [SOURCE], "openai")

    async def stream_answer(self, question, chunks):
        try:
            yield "Do not "
            await asyncio.sleep(0)
            yield "share."
            yield self.answer(question, chunks)
        finally:
            self.closed = True


def service(answerer=None):
    return AssistantService(
        retriever=SimpleNamespace(retrieve_filtered=lambda *args, **kwargs: [CHUNK]),
        router=SimpleNamespace(
            route=lambda *args: RoutingResult(
                ["northstar-ai-acceptable-use-policy"], "heuristic", "AI policy"
            )
        ),
        answerers={"openai": answerer or FakeAnswerer()},
    )


class ServiceStreamingTests(unittest.IsolatedAsyncioTestCase):
    async def test_yields_deltas_before_complete_result_with_evidence(self):
        stream = service().stream_question("Can I share?", answer_provider="openai")
        self.assertEqual((await anext(stream)).text, "Do not ")
        self.assertEqual((await anext(stream)).text, "share.")
        result = await anext(stream)
        self.assertEqual(result.answer, "Do not share.")
        self.assertEqual(result.sources[0]["chunk_id"], CHUNK.chunk_id)
        self.assertEqual(result.routed_documents[0]["title"], "AI Acceptable Use Policy")
        await stream.aclose()

    async def test_closing_consumer_closes_answer_stream(self):
        answerer = FakeAnswerer()
        stream = service(answerer).stream_question("Question", answer_provider="openai")
        await anext(stream)
        await stream.aclose()
        self.assertTrue(answerer.closed)


class RouteStreamingTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.dependency_overrides[get_assistant_service] = service
        self.client = TestClient(self.app)

    def events(self, body):
        return [frame for frame in body.split("\n\n") if frame.startswith("event:")]

    def test_sse_contract_and_existing_json_response_agree(self):
        payload = {"question": "Can I share?", "answer_provider": "openai"}
        response = self.client.post("/api/ask/stream", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers["content-type"])
        self.assertEqual(response.headers["x-accel-buffering"], "no")
        frames = self.events(response.text)
        self.assertEqual(
            [frame.splitlines()[0] for frame in frames],
            ["event: delta", "event: delta", "event: result"],
        )
        result = json.loads(frames[-1].split("data: ", 1)[1])
        self.assertEqual(result, self.client.post("/api/ask", json=payload).json())

    def test_blank_and_invalid_provider_fail_before_streaming(self):
        self.assertEqual(
            self.client.post("/api/ask/stream", json={"question": "  "}).status_code, 400
        )
        self.assertEqual(
            self.client.post(
                "/api/ask/stream", json={"question": "Q", "answer_provider": "other"}
            ).status_code,
            422,
        )

    def test_midstream_error_is_terminal_and_does_not_leak_exception(self):
        class Broken(FakeAnswerer):
            async def stream_answer(self, question, chunks):
                yield "Partial"
                raise RuntimeError("private provider diagnostic")

        self.app.dependency_overrides[get_assistant_service] = lambda: service(Broken())
        response = self.client.post(
            "/api/ask/stream", json={"question": "Q", "answer_provider": "openai"}
        )
        frames = self.events(response.text)
        self.assertEqual([f.splitlines()[0] for f in frames], ["event: delta", "event: error"])
        self.assertNotIn("private provider diagnostic", response.text)


class ProviderStreamingTests(unittest.IsolatedAsyncioTestCase):
    async def test_no_context_finishes_without_calling_openai(self):
        answerer = OpenAIAnswerer("test-key", "test-model")
        result = [event async for event in answerer.stream_answer("Question", [])]
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].sources, [])
        self.assertIn("could not find", result[0].answer)

    async def test_streams_sdk_deltas_and_closes_client_and_stream(self):
        chunks = [
            SimpleNamespace(
                choices=[SimpleNamespace(delta=SimpleNamespace(content=text), finish_reason=reason)]
            )
            for text, reason in [(None, None), ("First ", None), ("second", None), (None, "stop")]
        ]

        class Stream:
            closed = False

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                self.closed = True

            def __aiter__(self):
                return self

            async def __anext__(self):
                if not chunks:
                    raise StopAsyncIteration
                return chunks.pop(0)

        stream = Stream()

        class Client:
            closed = False

            def __init__(self, **kwargs):
                self.chat = SimpleNamespace(completions=self)

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                self.closed = True

            async def create(self, **kwargs):
                self.options = kwargs
                return stream

        client = Client()
        with patch("openai.AsyncOpenAI", return_value=client):
            result = [
                event
                async for event in OpenAIAnswerer("test-key", "test-model").stream_answer(
                    "Question", [CHUNK]
                )
            ]
        self.assertEqual(result[:2], ["First ", "second"])
        self.assertEqual(result[-1].answer, "First second")
        self.assertTrue(stream.closed)
        self.assertTrue(client.closed)
        self.assertTrue(client.options["stream"])
        self.assertIn(CHUNK.text, client.options["messages"][-1]["content"])
