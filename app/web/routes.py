from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.assistant import AssistantService, build_default_assistant_service
from app.config import get_settings
from app.retrieval.answerer import AnswerProviderError
from app.web.schemas import AskRequest, AskResponse


router = APIRouter()
STATIC_DIR = Path(__file__).parent / "static"


def get_assistant_service() -> AssistantService:
    return build_default_assistant_service()


@router.get("/", response_class=FileResponse, tags=["web"])
def root() -> FileResponse:
    index = STATIC_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=503, detail="The web interface is not available.")
    return FileResponse(index, headers={"Cache-Control": "no-cache"})


@router.get("/api/status", tags=["system"])
def status() -> dict[str, object]:
    settings = get_settings()
    return {
        "name": "Policy RAG Assistant",
        "status": "ready",
        "documents_dir": str(settings.documents_dir),
        "vector_store_dir": str(settings.vector_store_dir),
    }


@router.post("/api/ask", response_model=AskResponse, tags=["assistant"])
def ask_question(
    request: AskRequest,
    assistant: AssistantService = Depends(get_assistant_service),
) -> AskResponse:
    try:
        response = assistant.answer_question(
            request.question,
            top_k=request.top_k,
            answer_provider=request.answer_provider,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AnswerProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return AskResponse(
        answer=response.answer,
        answer_provider=response.answer_provider,
        routed_documents=response.routed_documents,
        routing_provider=response.routing_provider,
        routing_rationale=response.routing_rationale,
        sources=response.sources,
        retrieved_chunks=response.retrieved_chunks,
    )
