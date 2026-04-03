from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, description="Natural-language question about company policy.")
    top_k: int | None = Field(default=None, ge=1, le=10)


class SourceResponse(BaseModel):
    document_name: str
    page_number: int
    chunk_id: str


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
    sources: list[SourceResponse]
    retrieved_chunks: list[RetrievedChunkResponse]
