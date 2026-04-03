from fastapi import APIRouter, Depends, HTTPException

from app.assistant import AssistantService, build_default_assistant_service
from app.config import get_settings
from app.web.schemas import AskRequest, AskResponse


router = APIRouter()


def get_assistant_service() -> AssistantService:
    return build_default_assistant_service()


@router.get("/", tags=["system"])
def root() -> dict[str, object]:
    settings = get_settings()
    return {
        "name": "Policy RAG Assistant",
        "status": "setup-complete",
        "documents_dir": str(settings.documents_dir),
        "vector_store_dir": str(settings.vector_store_dir),
    }


@router.post("/api/ask", response_model=AskResponse, tags=["assistant"])
def ask_question(
    request: AskRequest,
    assistant: AssistantService = Depends(get_assistant_service),
) -> AskResponse:
    try:
        response = assistant.answer_question(request.question, top_k=request.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return AskResponse(
        answer=response.answer,
        answer_provider=response.answer_provider,
        sources=response.sources,
        retrieved_chunks=response.retrieved_chunks,
    )
