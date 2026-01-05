from fastapi import FastAPI

from app.api.routes import router as api_router
from app.api.status import router as status_router
from app.api.processing import router as processing_router
from app.api import documents, search, chat, generation, web_search
from app.api.search import router as search_router
from app.api.chat import router as chat_router
from app.api.generation import router as generation_router
from app.api.web_search import router as web_search_router
from app.config import settings
from app.utils.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging(settings.log_level)
    app = FastAPI(title="Curious Concierge API", version="0.1.0")

    app.include_router(api_router, prefix="/api")
    app.include_router(status_router, prefix="/api")
    app.include_router(processing_router, prefix="/api")
    app.include_router(documents.router, prefix="/api")
    app.include_router(search_router)
    app.include_router(chat_router)
    app.include_router(generation_router)
    app.include_router(web_search_router)

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
