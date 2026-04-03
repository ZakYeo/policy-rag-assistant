from __future__ import annotations

import json
from dataclasses import dataclass

from app.config import get_settings
from app.retrieval.catalog import POLICY_DOCUMENTS, PolicyDocument


@dataclass(slots=True)
class RoutingResult:
    document_ids: list[str]
    provider: str
    rationale: str


class DocumentRouterError(RuntimeError):
    """Raised when document routing cannot be completed cleanly."""


class OpenAIDocumentRouter:
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise DocumentRouterError(
                "OpenAI routing is selected but OPENAI_API_KEY is not configured on the backend."
            )

        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def route(self, question: str, documents: list[PolicyDocument]) -> RoutingResult:
        document_listing = "\n".join(
            [
                f"- {document.document_id}: {document.title}. {document.summary}"
                for document in documents
            ]
        )
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You route policy questions to the most relevant documents. "
                            "Return strict JSON with keys document_ids and rationale. "
                            "document_ids must be a non-empty array of document_id values taken "
                            "from the provided catalog. Select one or more documents when needed."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Question: {question}\n\nCatalog:\n{document_listing}",
                    },
                ],
            )
        except Exception as exc:
            raise DocumentRouterError(
                "The OpenAI document router failed. Check backend configuration, API key, "
                "network access, or account quota."
            ) from exc

        payload = json.loads(response.choices[0].message.content or "{}")
        selected_ids = payload.get("document_ids") or []
        valid_ids = {document.document_id for document in documents}
        filtered_ids = [document_id for document_id in selected_ids if document_id in valid_ids]
        if not filtered_ids:
            raise DocumentRouterError("The OpenAI document router returned no valid documents.")

        return RoutingResult(
            document_ids=filtered_ids,
            provider="openai",
            rationale=str(payload.get("rationale", "")).strip(),
        )


class HeuristicDocumentRouter:
    KEYWORD_MAP = {
        "northstar-ai-acceptable-use-policy": {
            "ai",
            "llm",
            "model",
            "prompt",
            "customer data",
            "public ai",
            "generative",
        },
        "northstar-employee-handbook": {
            "attendance",
            "leave",
            "manager",
            "remote work",
            "probation",
            "conduct",
            "employee",
            "working hours",
        },
        "northstar-information-security-policy": {
            "security",
            "incident",
            "restricted",
            "confidential",
            "password",
            "mfa",
            "device",
            "laptop",
            "lost",
            "stolen",
            "vpn",
            "data handling",
        },
    }

    def route(self, question: str, documents: list[PolicyDocument]) -> RoutingResult:
        lowered = question.lower()
        scores: list[tuple[int, PolicyDocument]] = []
        for document in documents:
            keywords = self.KEYWORD_MAP.get(document.document_id, set())
            score = sum(1 for keyword in keywords if keyword in lowered)
            scores.append((score, document))

        scores.sort(key=lambda item: item[0], reverse=True)
        selected = [document.document_id for score, document in scores if score > 0]
        if not selected:
            selected = [document.document_id for _, document in scores[:2]]

        return RoutingResult(
            document_ids=selected,
            provider="heuristic",
            rationale="Fallback heuristic routing based on question keywords.",
        )


def build_default_router():
    settings = get_settings()
    if settings.router_provider == "openai":
        try:
            return OpenAIDocumentRouter(
                api_key=settings.openai_api_key,
                model=settings.openai_chat_model,
            )
        except DocumentRouterError:
            return HeuristicDocumentRouter()
    if settings.router_provider == "heuristic":
        return HeuristicDocumentRouter()

    raise DocumentRouterError(
        f"Unsupported router provider: {settings.router_provider}. "
        "Expected 'openai' or 'heuristic'."
    )
