from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.api.models.Collection import Collection

from app.config import get_settings
from app.retrieval.embeddings import Embedder, build_default_embedder


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_name: str
    source_path: str
    page_number: int
    chunk_index: int
    char_start: int
    char_end: int
    text: str
    distance: float


class ChunkRetriever:
    def __init__(
        self,
        persist_dir: Path,
        collection_name: str,
        embedder: Embedder,
        collection: Collection | None = None,
    ) -> None:
        self._embedder = embedder
        if collection is not None:
            self._collection = collection
            return

        client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
        query = query.strip()
        if not query:
            return []

        query_embedding = self._embedder.embed_texts([query])[0]
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        retrieved_chunks: list[RetrievedChunk] = []
        ids = result["ids"][0]
        documents = result["documents"][0]
        metadatas = result["metadatas"][0]
        distances = result["distances"][0]

        for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
            retrieved_chunks.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    document_id=str(metadata["document_id"]),
                    document_name=str(metadata["document_name"]),
                    source_path=str(metadata["source_path"]),
                    page_number=int(metadata["page_number"]),
                    chunk_index=int(metadata["chunk_index"]),
                    char_start=int(metadata["char_start"]),
                    char_end=int(metadata["char_end"]),
                    text=document,
                    distance=float(distance),
                )
            )

        return retrieved_chunks


def build_default_retriever() -> ChunkRetriever:
    settings = get_settings()
    return ChunkRetriever(
        persist_dir=settings.vector_store_dir,
        collection_name=settings.vector_store_collection,
        embedder=build_default_embedder(),
    )
