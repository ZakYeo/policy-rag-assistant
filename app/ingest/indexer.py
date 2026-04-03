from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.api.models.Collection import Collection

from app.config import get_settings
from app.ingest.chunker import Chunk
from app.retrieval.embeddings import Embedder, build_default_embedder


class ChunkIndexer:
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
            self._client = None
            self._collection_name = collection.name
            return

        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection_name = collection_name
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(self, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0

        embeddings = self._embedder.embed_texts([chunk.text for chunk in chunks])
        metadatas = [
            {
                "document_id": chunk.document_id,
                "document_name": chunk.document_name,
                "source_path": chunk.source_path,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "char_start": chunk.char_start,
                "char_end": chunk.char_end,
            }
            for chunk in chunks
        ]

        self._collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return len(chunks)

    def count(self) -> int:
        return self._collection.count()

    def reset(self) -> None:
        if self._client is None:
            existing = self._collection.get(include=[])
            if existing["ids"]:
                self._collection.delete(ids=existing["ids"])
            return

        try:
            self._client.delete_collection(name=self._collection_name)
        except Exception:
            pass
        self._collection = self._client.get_or_create_collection(name=self._collection_name)


def build_default_indexer() -> ChunkIndexer:
    settings = get_settings()
    return ChunkIndexer(
        persist_dir=settings.vector_store_dir,
        collection_name=settings.vector_store_collection,
        embedder=build_default_embedder(),
    )
