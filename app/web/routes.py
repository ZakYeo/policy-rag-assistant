from pathlib import Path
from contextlib import aclosing
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse

from app.assistant import AnswerDelta, AssistantService, build_default_assistant_service
from app.config import get_settings
from app.retrieval.answerer import AnswerProviderError
from app.web.schemas import AskRequest, AskResponse


router = APIRouter()
STATIC_DIR = Path(__file__).parent / "static"
logger = logging.getLogger(__name__)


def get_assistant_service() -> AssistantService:
    return build_default_assistant_service()


@router.get("/policies", response_class=FileResponse, tags=["web"])
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


@router.post("/api/ask/stream", tags=["assistant"])
async def stream_question(
    payload: AskRequest,
    request: Request,
    assistant: AssistantService = Depends(get_assistant_service),
) -> StreamingResponse:
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty")

    async def events():
        # Send headers promptly while routing and retrieval execute off the event loop.
        yield ": stream-start\n\n"
        try:
            async with aclosing(
                assistant.stream_question(
                    payload.question,
                    top_k=payload.top_k,
                    answer_provider=payload.answer_provider,
                )
            ) as stream:
                async for event in stream:
                    if await request.is_disconnected():
                        return
                    if isinstance(event, AnswerDelta):
                        yield _event("delta", {"text": event.text})
                    else:
                        response = AskResponse.model_validate(event, from_attributes=True)
                        yield _event("result", response.model_dump())
                        return
        except AnswerProviderError as exc:
            yield _event("error", {"message": str(exc)})
        except Exception as exc:
            logger.warning("Policy stream failed (%s)", type(exc).__name__)
            yield _event(
                "error", {"message": "The answer could not be completed. Please try again."}
            )

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


def _event(name: str, data: dict) -> str:
    return f"event: {name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
