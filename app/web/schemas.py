from typing import Literal

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, description="Natural-language question about company policy.")
    top_k: int | None = Field(default=None, ge=1, le=10)
    answer_provider: Literal["openai", "extractive"] | None = None


class SourceResponse(BaseModel):
    document_name: str
    page_number: int
    chunk_id: str


class RoutedDocumentResponse(BaseModel):
    document_id: str
    document_name: str
    title: str


class RetrievedChunkResponse(BaseModel):
    chunk_id: str
    document_name: str
    page_number: int
    chunk_index: int
    distance: float
    text: str


class AskResponse(BaseModel):
    answer: str
    answer_provider: str
    routed_documents: list[RoutedDocumentResponse]
    routing_provider: str
    routing_rationale: str
    sources: list[SourceResponse]
    retrieved_chunks: list[RetrievedChunkResponse]
