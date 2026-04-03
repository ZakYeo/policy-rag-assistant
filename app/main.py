from fastapi import FastAPI

from app.config import get_settings
from app.web.routes import router as web_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Policy RAG Assistant",
        version="0.1.0",
        summary="Internal policy assistant powered by retrieval-augmented generation.",
    )
    app.include_router(web_router)

    @app.get("/health", tags=["system"])
    def healthcheck() -> dict[str, str]:
        return {
            "status": "ok",
            "environment": settings.app_env,
        }

    return app


app = create_app()
