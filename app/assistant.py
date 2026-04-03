from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings
from app.retrieval.answerer import AnswerProviderError, build_default_answerer
from app.retrieval.catalog import POLICY_DOCUMENTS
from app.retrieval.retriever import RetrievedChunk, build_default_retriever
from app.retrieval.router import build_default_router


@dataclass(slots=True)
class AssistantResponse:
    answer: str
    answer_provider: str
    routed_documents: list[dict[str, object]]
    routing_provider: str
    routing_rationale: str
    sources: list[dict[str, object]]
    retrieved_chunks: list[dict[str, object]]


class AssistantService:
    def __init__(
        self,
        retriever=None,
        router=None,
        answerers: dict[str, object] | None = None,
    ) -> None:
        self._retriever = retriever or build_default_retriever()
        self._router = router or build_default_router()
        self._answerers = answerers or {}

    def answer_question(
        self,
        question: str,
        top_k: int | None = None,
        answer_provider: str | None = None,
    ) -> AssistantResponse:
        clean_question = question.strip()
        if not clean_question:
            raise ValueError("Question must not be empty")

        settings = get_settings()
        retrieval_limit = top_k or settings.retrieval_top_k
        routing_result = self._router.route(clean_question, POLICY_DOCUMENTS)
        chunks = self._retriever.retrieve_filtered(
            clean_question,
            top_k=retrieval_limit,
            document_ids=routing_result.document_ids,
        )
        selected_provider = answer_provider or settings.answer_provider
        answerer = self._answerers.get(selected_provider)
        if answerer is None:
            answerer = build_default_answerer(selected_provider)

        answer_result = answerer.answer(clean_question, chunks)
        return AssistantResponse(
            answer=answer_result.answer,
            answer_provider=answer_result.provider,
            routed_documents=[
                _serialize_document(document_id)
                for document_id in routing_result.document_ids
            ],
            routing_provider=routing_result.provider,
            routing_rationale=routing_result.rationale,
            sources=[
                {
                    "document_name": source.document_name,
                    "page_number": source.page_number,
                    "chunk_id": source.chunk_id,
                }
                for source in answer_result.sources
            ],
            retrieved_chunks=[
                _serialize_chunk(chunk)
                for chunk in chunks
            ],
        )


def _serialize_chunk(chunk: RetrievedChunk) -> dict[str, object]:
    return {
        "chunk_id": chunk.chunk_id,
        "document_name": chunk.document_name,
        "page_number": chunk.page_number,
        "chunk_index": chunk.chunk_index,
        "distance": chunk.distance,
        "text": chunk.text,
    }


def _serialize_document(document_id: str) -> dict[str, object]:
    document = next(
        document for document in POLICY_DOCUMENTS if document.document_id == document_id
    )
    return {
        "document_id": document.document_id,
        "document_name": document.document_name,
        "title": document.title,
    }


def build_default_assistant_service() -> AssistantService:
    return AssistantService()
