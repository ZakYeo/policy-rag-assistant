from __future__ import annotations

import hashlib
import math
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


class LocalHashEmbedder:
    def __init__(self, dimensions: int = 256) -> None:
        self._dimensions = dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in texts]

    def _embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self._dimensions
        tokens = text.lower().split()
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self._dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            weight = 1.0 + (digest[5] / 255.0)
            vector[index] += sign * weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


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
        self._collection = self._client.get_or_create_collection(name=collection_name)

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
    if settings.embedding_provider == "openai":
        embedder: Embedder = OpenAIEmbedder(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
        )
    elif settings.embedding_provider == "local":
        embedder = LocalHashEmbedder()
    else:
        raise ValueError(
            f"Unsupported embedding provider: {settings.embedding_provider}. "
            "Expected 'local' or 'openai'."
        )

    return ChunkIndexer(
        persist_dir=settings.vector_store_dir,
        collection_name=settings.vector_store_collection,
        embedder=embedder,
    )
