from fastapi import APIRouter

from app.config import get_settings


router = APIRouter()


@router.get("/", tags=["system"])
def root() -> dict[str, object]:
    settings = get_settings()
    return {
        "name": "Policy RAG Assistant",
        "status": "setup-complete",
        "documents_dir": str(settings.documents_dir),
        "vector_store_dir": str(settings.vector_store_dir),
    }
