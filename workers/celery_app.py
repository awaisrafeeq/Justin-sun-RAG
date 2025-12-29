from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "rag_workers",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_routes={
        "workers.tasks.process_pdf": {"queue": "ingestion"},
        "workers.tasks.process_episode": {"queue": "ingestion"},
    },
)
