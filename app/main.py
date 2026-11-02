from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.policies.routes import router as policy_router, operation_router
from app.policies.preview_routes import router as preview_router
from app.config import get_settings
from app.web.routes import router as web_router
from app.web.routes import STATIC_DIR


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Policy RAG Assistant",
        version="0.1.0",
        summary="Internal policy assistant powered by retrieval-augmented generation.",
    )
    app.include_router(web_router)
    app.include_router(policy_router)
    app.include_router(operation_router)
    app.include_router(preview_router)
    app.mount(
        "/assets", StaticFiles(directory=STATIC_DIR / "assets", check_dir=False), name="assets"
    )
    app.mount(
        "/licenses",
        StaticFiles(directory=STATIC_DIR / "licenses", check_dir=False),
        name="licenses",
    )

    @app.get("/health", tags=["system"])
    def healthcheck() -> dict[str, str]:
        return {
            "status": "ok",
            "environment": settings.app_env,
        }

    return app


app = create_app()
