"""Deterministic HTTP streaming fixture. Never mounted by the production app."""

import asyncio
from dataclasses import asdict
from tempfile import TemporaryDirectory
from pathlib import Path
from app.policies.library import PolicyLibrary
from app.policies.routes import library_dependency
from app.retrieval.embeddings import LocalHashEmbedder

from fastapi import HTTPException

from app.assistant import AnswerDelta, AssistantResponse, AssistantService
from app.main import create_app
from app.web.routes import get_assistant_service

fixture_directory = TemporaryDirectory(prefix="policy-browser-")
fixture_library = PolicyLibrary(Path(fixture_directory.name), Path("documents"), LocalHashEmbedder())
fixture_library.initialize()
app = create_app()
app.dependency_overrides[library_dependency] = lambda: fixture_library
gates: dict[str, asyncio.Event] = {}
fixture_response = AssistantResponse(
    answer="First part. Complete answer.",
    answer_provider="openai",
    routing_provider="heuristic",
    routing_rationale="Browser test fixture",
    routed_documents=[
        {
            "document_id": "northstar-ai-acceptable-use-policy",
            "document_name": "northstar-ai-acceptable-use-policy.pdf",
            "title": "AI Acceptable Use Policy",
        }
    ],
    sources=[
        {
            "document_name": "northstar-ai-acceptable-use-policy.pdf",
            "page_number": 1,
            "chunk_id": "test-p1-c0",
        }
    ],
    retrieved_chunks=[
        {
            "document_name": "northstar-ai-acceptable-use-policy.pdf",
            "page_number": 1,
            "chunk_id": "test-p1-c0",
            "chunk_index": 0,
            "distance": 0.1,
            "text": "Do not upload customer data to public AI tools.",
        }
    ],
)


class BrowserService:
    def answer_question(self, question, top_k=None, answer_provider=None):
        return AssistantService(library=fixture_library).answer_question(question, top_k, answer_provider)

    async def stream_question(self, question, top_k=None, answer_provider=None):
        if question not in {"stream success", "stream failure"}:
            raise ValueError("Unexpected browser fixture question")
        gate = asyncio.Event()
        gates[question] = gate
        try:
            yield AnswerDelta("First part. ")
            await gate.wait()
            if question == "stream failure":
                raise RuntimeError("Simulated transport interruption")
            yield AnswerDelta("Complete answer.")
            yield fixture_response
        finally:
            gates.pop(question, None)


app.dependency_overrides[get_assistant_service] = BrowserService


@app.post("/__test__/release/{outcome}")
async def release(outcome: str):
    gate = gates.get(f"stream {outcome}")
    if gate is None:
        raise HTTPException(409, "No pending fixture stream")
    gate.set()
    return {"released": True}


@app.get("/__test__/response")
def response():
    return asdict(fixture_response)
