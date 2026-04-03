from __future__ import annotations

from pathlib import Path
from typing import Protocol

import chromadb
from chromadb.api.models.Collection import Collection

from app.config import get_settings
from app.ingest.chunker import Chunk


class Embedder(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...


class OpenAIEmbedder:
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for embedding generation")

        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in response.data]


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
            return

        client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = client.get_or_create_collection(name=collection_name)

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


def build_default_indexer() -> ChunkIndexer:
    settings = get_settings()
    return ChunkIndexer(
        persist_dir=settings.vector_store_dir,
        collection_name=settings.vector_store_collection,
        embedder=OpenAIEmbedder(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
        ),
    )
