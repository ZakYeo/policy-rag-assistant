from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings
from app.retrieval.answerer import AnswerResult, build_default_answerer
from app.retrieval.retriever import RetrievedChunk, build_default_retriever


@dataclass(slots=True)
class AssistantResponse:
    answer: str
    answer_provider: str
    sources: list[dict[str, object]]
    retrieved_chunks: list[dict[str, object]]


class AssistantService:
    def __init__(self, retriever=None, answerer=None) -> None:
        self._retriever = retriever or build_default_retriever()
        self._answerer = answerer or build_default_answerer()

    def answer_question(self, question: str, top_k: int | None = None) -> AssistantResponse:
        clean_question = question.strip()
        if not clean_question:
            raise ValueError("Question must not be empty")

        settings = get_settings()
        retrieval_limit = top_k or settings.retrieval_top_k
        chunks = self._retriever.retrieve(clean_question, top_k=retrieval_limit)
        answer_result = self._answerer.answer(clean_question, chunks)
        return AssistantResponse(
            answer=answer_result.answer,
            answer_provider=answer_result.provider,
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


def build_default_assistant_service() -> AssistantService:
    return AssistantService()
