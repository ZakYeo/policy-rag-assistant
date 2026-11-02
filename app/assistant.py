from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import aclosing, nullcontext
from dataclasses import dataclass

from app.config import get_settings
from app.retrieval.answerer import AnswerResult, build_default_answerer
from app.retrieval.catalog import POLICY_DOCUMENTS
from app.retrieval.retriever import RetrievedChunk, build_default_retriever
from app.retrieval.router import RoutingResult, build_default_router


@dataclass(slots=True)
class AssistantResponse:
    answer: str
    answer_provider: str
    routed_documents: list[dict[str, object]]
    routing_provider: str
    routing_rationale: str
    sources: list[dict[str, object]]
    retrieved_chunks: list[dict[str, object]]


@dataclass(slots=True)
class AnswerDelta:
    text: str


@dataclass(slots=True)
class PreparedQuestion:
    question: str
    routing: RoutingResult
    chunks: list[RetrievedChunk]
    answerer: object
    documents: list


class AssistantService:
    def __init__(
        self,
        retriever=None,
        router=None,
        answerers: dict[str, object] | None = None,
        library=None,
    ) -> None:
        self._library = library
        self._retriever = retriever or build_default_retriever()
        self._router = router or build_default_router()
        self._answerers = answerers or {}

    def answer_question(
        self,
        question: str,
        top_k: int | None = None,
        answer_provider: str | None = None,
    ) -> AssistantResponse:
        prepared = self._prepare(question, top_k, answer_provider)
        result = prepared.answerer.answer(prepared.question, prepared.chunks)
        return self._response(prepared, result)

    async def stream_question(
        self,
        question: str,
        top_k: int | None = None,
        answer_provider: str | None = None,
    ) -> AsyncIterator[AnswerDelta | AssistantResponse]:
        prepared = await asyncio.to_thread(self._prepare, question, top_k, answer_provider)
        if not hasattr(prepared.answerer, "stream_answer"):
            result = await asyncio.to_thread(
                prepared.answerer.answer, prepared.question, prepared.chunks
            )
            yield self._response(prepared, result)
            return
        async with aclosing(
            prepared.answerer.stream_answer(prepared.question, prepared.chunks)
        ) as stream:
            async for event in stream:
                if isinstance(event, str):
                    yield AnswerDelta(event)
                else:
                    yield self._response(prepared, event)

    def _prepare(self, question, top_k, answer_provider) -> PreparedQuestion:
        clean_question = question.strip()
        if not clean_question:
            raise ValueError("Question must not be empty")

        settings = get_settings()
        retrieval_limit = top_k or settings.retrieval_top_k
        snapshot = self._library.snapshot() if self._library else nullcontext((POLICY_DOCUMENTS, self._retriever))
        with snapshot as (documents, retriever):
            routing_result = self._router.route(clean_question, documents) if documents else RoutingResult([], "none", "No policies uploaded.")
            chunks = retriever.retrieve_filtered(
                clean_question, top_k=retrieval_limit, document_ids=routing_result.document_ids,
            ) if documents else []
        selected_provider = answer_provider or settings.answer_provider
        answerer = self._answerers.get(selected_provider)
        if answerer is None:
            answerer = build_default_answerer(selected_provider)

        return PreparedQuestion(clean_question, routing_result, chunks, answerer, documents)

    @staticmethod
    def _response(prepared: PreparedQuestion, answer_result: AnswerResult) -> AssistantResponse:
        return AssistantResponse(
            answer=answer_result.answer,
            answer_provider=answer_result.provider,
            routed_documents=[
                _serialize_document(document_id, prepared.documents) for document_id in prepared.routing.document_ids
            ],
            routing_provider=prepared.routing.provider,
            routing_rationale=prepared.routing.rationale,
            sources=[
                {
                    "document_name": source.document_name,
                    "page_number": source.page_number,
                    "chunk_id": source.chunk_id,
                    "location": next((getattr(chunk, "location", "") for chunk in prepared.chunks if chunk.chunk_id == source.chunk_id), ""),
                }
                for source in answer_result.sources
            ],
            retrieved_chunks=[_serialize_chunk(chunk) for chunk in prepared.chunks],
        )


def _serialize_chunk(chunk: RetrievedChunk) -> dict[str, object]:
    return {
        "chunk_id": chunk.chunk_id,
        "document_name": chunk.document_name,
        "page_number": chunk.page_number,
        "chunk_index": chunk.chunk_index,
        "distance": chunk.distance,
        "location": getattr(chunk, "location", ""),
        "text": chunk.text,
    }


def _serialize_document(document_id: str, documents=POLICY_DOCUMENTS) -> dict[str, object]:
    document = next(
        document for document in documents if document.document_id == document_id
    )
    return {
        "document_id": document.document_id,
        "document_name": document.document_name,
        "title": document.title,
    }


def build_default_assistant_service() -> AssistantService:
    from app.policies.library import get_library

    return AssistantService(library=get_library())
