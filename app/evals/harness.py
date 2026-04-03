from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.assistant import AssistantService
from app.ingest.chunker import chunk_documents, write_chunk_output
from app.ingest.extractor import extract_all_documents, write_extraction_output
from app.ingest.indexer import ChunkIndexer
from app.retrieval.answerer import ExtractiveAnswerer
from app.retrieval.catalog import POLICY_DOCUMENTS
from app.retrieval.embeddings import LocalHashEmbedder
from app.retrieval.retriever import ChunkRetriever
from app.retrieval.router import HeuristicDocumentRouter


@dataclass(slots=True)
class IntegrationRunResult:
    answer: str
    answer_provider: str
    routed_documents: list[dict[str, object]]
    routing_provider: str
    routing_rationale: str
    sources: list[dict[str, object]]
    retrieved_chunks: list[dict[str, object]]


class RagIntegrationHarness:
    def __init__(
        self,
        documents_dir: Path,
        chunk_size: int = 900,
        chunk_overlap: int = 150,
    ) -> None:
        self._documents_dir = documents_dir
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._tempdir = tempfile.TemporaryDirectory(prefix="policy-rag-eval-")
        self.workspace = Path(self._tempdir.name)
        self.extracted_output = self.workspace / "extracted" / "documents.json"
        self.chunk_output = self.workspace / "chunks" / "chunks.json"
        self.vector_store_dir = self.workspace / "chroma"

        self.documents = extract_all_documents(self._documents_dir)
        write_extraction_output(self.documents, self.extracted_output)

        self.chunks = chunk_documents(
            self.documents,
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
        )
        write_chunk_output(self.chunks, self.chunk_output)

        self.embedder = LocalHashEmbedder()
        self.indexer = ChunkIndexer(
            persist_dir=self.vector_store_dir,
            collection_name="policy_chunks_eval",
            embedder=self.embedder,
        )
        self.indexer.upsert_chunks(self.chunks)

        self.retriever = ChunkRetriever(
            persist_dir=self.vector_store_dir,
            collection_name="policy_chunks_eval",
            embedder=self.embedder,
        )
        self.router = HeuristicDocumentRouter()
        self.answerer = ExtractiveAnswerer()
        self.assistant = AssistantService(
            retriever=self.retriever,
            router=self.router,
            answerers={"extractive": self.answerer},
        )

    def close(self) -> None:
        self._tempdir.cleanup()

    def run_question(self, question: str, top_k: int = 4) -> IntegrationRunResult:
        response = self.assistant.answer_question(
            question,
            top_k=top_k,
            answer_provider="extractive",
        )
        return IntegrationRunResult(
            answer=response.answer,
            answer_provider=response.answer_provider,
            routed_documents=response.routed_documents,
            routing_provider=response.routing_provider,
            routing_rationale=response.routing_rationale,
            sources=response.sources,
            retrieved_chunks=response.retrieved_chunks,
        )

    @property
    def document_catalog(self) -> list[dict[str, str]]:
        return [
            {
                "document_id": document.document_id,
                "document_name": document.document_name,
                "title": document.title,
            }
            for document in POLICY_DOCUMENTS
        ]
