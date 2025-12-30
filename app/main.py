from fastapi import FastAPI

from app.api.routes import router as api_router
from app.api.status import router as status_router
from app.api.processing import router as processing_router
from app.api.documents import router as documents_router
from app.config import settings
from app.utils.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging(settings.log_level)
    app = FastAPI(title="Curious Concierge API", version="0.1.0")

    app.include_router(api_router, prefix="/api")
    app.include_router(status_router, prefix="/api")
    app.include_router(processing_router, prefix="/api")
    app.include_router(documents_router, prefix="/api")

    @app.get("/health")
    async def health_check():
        return {
            "status": "ok",
            "environment": settings.app_env,
            "services": {
                "postgres": settings.postgres_host,
                "redis": settings.redis_host,
                "qdrant": settings.qdrant_host,
            },
        }

    return app


app = create_app()
