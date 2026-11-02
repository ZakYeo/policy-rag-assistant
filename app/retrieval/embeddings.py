from __future__ import annotations

import hashlib
import math
from typing import Protocol

from app.config import get_settings
from app.retrieval.embedding_inputs import embedding_batches


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

        accumulated: list[list[float] | None] = [None] * len(texts)
        for batch in embedding_batches(texts):
            response = self._client.embeddings.create(model=self._model, input=[piece for _, piece, _ in batch])
            data = sorted(response.data, key=lambda item: item.index)
            if [item.index for item in data] != list(range(len(batch))):
                raise RuntimeError('The embedding service returned incomplete vectors.')
            for (owner, _, weight), item in zip(batch, data):
                vector = item.embedding
                if not vector or not all(math.isfinite(value) for value in vector):
                    raise RuntimeError('The embedding service returned an invalid vector.')
                total = accumulated[owner]
                if total is None:
                    total = accumulated[owner] = [0.0] * len(vector)
                if len(total) != len(vector):
                    raise RuntimeError('The embedding service returned inconsistent dimensions.')
                for index, value in enumerate(vector):
                    total[index] += value * weight
        result = []
        for total in accumulated:
            if total is None:
                raise RuntimeError('The embedding service returned no vector.')
            norm = math.sqrt(sum(value * value for value in total))
            if not norm:
                raise RuntimeError('The embedding service returned an empty vector.')
            # Weighted averaging then normalisation equals normalising the weighted sum.
            result.append([value / norm for value in total])
        return result


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


def build_default_embedder() -> Embedder:
    settings = get_settings()
    if settings.embedding_provider == "openai":
        return OpenAIEmbedder(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
        )
    if settings.embedding_provider == "local":
        return LocalHashEmbedder()

    raise ValueError(
        f"Unsupported embedding provider: {settings.embedding_provider}. "
        "Expected 'local' or 'openai'."
    )
