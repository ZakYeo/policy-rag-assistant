from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import get_settings
from app.retrieval.retriever import RetrievedChunk


TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(slots=True)
class AnswerSource:
    document_name: str
    page_number: int
    chunk_id: str


@dataclass(slots=True)
class AnswerResult:
    answer: str
    sources: list[AnswerSource]
    provider: str


class AnswerProviderError(RuntimeError):
    """Raised when the selected answer provider cannot answer the request."""


class ExtractiveAnswerer:
    def answer(self, question: str, chunks: list[RetrievedChunk]) -> AnswerResult:
        if not chunks:
            return AnswerResult(
                answer=(
                    "I could not find supporting policy context for that question in the current "
                    "document set."
                ),
                sources=[],
                provider="extractive",
            )

        query_tokens = set(TOKEN_RE.findall(question.lower()))
        selected_snippets: list[tuple[str, RetrievedChunk]] = []
        seen_snippets: set[str] = set()

        ranked_chunks = sorted(
            chunks,
            key=lambda chunk: (
                len(query_tokens & set(TOKEN_RE.findall(chunk.text.lower()))),
                -chunk.distance,
            ),
            reverse=True,
        )

        for chunk in ranked_chunks:
            snippet = self._build_snippet(chunk.text, query_tokens)
            if snippet in seen_snippets:
                continue
            selected_snippets.append((snippet, chunk))
            seen_snippets.add(snippet)
            if len(selected_snippets) == 2:
                break

        if not selected_snippets:
            selected_snippets = [(self._build_snippet(chunks[0].text, query_tokens), chunks[0])]

        answer_parts = []
        sources: list[AnswerSource] = []
        for snippet, chunk in selected_snippets:
            citation = f"[{chunk.document_name} p.{chunk.page_number}]"
            answer_parts.append(f"{snippet} {citation}")
            sources.append(
                AnswerSource(
                    document_name=chunk.document_name,
                    page_number=chunk.page_number,
                    chunk_id=chunk.chunk_id,
                )
            )

        return AnswerResult(
            answer=" ".join(answer_parts),
            sources=sources,
            provider="extractive",
        )

    def _build_snippet(self, text: str, query_tokens: set[str], max_chars: int = 220) -> str:
        lowered = text.lower()
        anchor_position = -1
        for token in sorted(query_tokens, key=len, reverse=True):
            position = lowered.find(token)
            if position >= 0:
                anchor_position = position
                break

        if anchor_position >= 0:
            start = max(0, anchor_position - 30)
        else:
            start = 0

        end = min(len(text), start + max_chars)

        if start > 0:
            previous_space = text.rfind(" ", 0, start)
            if previous_space != -1:
                start = previous_space + 1
        if end < len(text):
            next_space = text.find(" ", end)
            if next_space != -1:
                end = next_space

        snippet = text[start:end].strip()
        if start > 0:
            snippet = f"... {snippet}"
        if end < len(text):
            snippet = f"{snippet} ..."
        return snippet


class OpenAIAnswerer:
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise AnswerProviderError(
                "OpenAI answering is selected but OPENAI_API_KEY is not configured on the backend."
            )

        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def answer(self, question: str, chunks: list[RetrievedChunk]) -> AnswerResult:
        if not chunks:
            return AnswerResult(
                answer=(
                    "I could not find supporting policy context for that question in the current "
                    "document set."
                ),
                sources=[],
                provider="openai",
            )

        context = "\n\n".join(
            [
                f"Source: {chunk.document_name} page {chunk.page_number}\n{chunk.text}"
                for chunk in chunks
            ]
        )
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a policy assistant. Answer only from the provided context. "
                            "If the context is insufficient, say so clearly. Cite sources inline "
                            "using the provided document names and page numbers."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Question: {question}\n\nContext:\n{context}",
                    },
                ],
            )
        except Exception as exc:
            raise AnswerProviderError(
                "The OpenAI answer provider failed. Check backend configuration, API key, "
                "network access, or account quota."
            ) from exc
        answer_text = response.choices[0].message.content or ""
        sources = [
            AnswerSource(
                document_name=chunk.document_name,
                page_number=chunk.page_number,
                chunk_id=chunk.chunk_id,
            )
            for chunk in chunks
        ]
        return AnswerResult(answer=answer_text, sources=sources, provider="openai")


def build_default_answerer(provider: str | None = None) -> ExtractiveAnswerer | OpenAIAnswerer:
    settings = get_settings()
    selected_provider = provider or settings.answer_provider
    if selected_provider == "extractive":
        return ExtractiveAnswerer()
    if selected_provider == "openai":
        return OpenAIAnswerer(
            api_key=settings.openai_api_key,
            model=settings.openai_chat_model,
        )

    raise AnswerProviderError(
        f"Unsupported answer provider: {selected_provider}. "
        "Expected 'extractive' or 'openai'."
    )
