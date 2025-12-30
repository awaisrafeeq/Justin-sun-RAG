from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "rag_workers",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["workers.tasks"],
    broker_connection_retry_on_startup=True,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_routes={
        "workers.tasks.process_pdf": {"queue": "ingestion"},
        "workers.tasks.process_episode": {"queue": "processing"},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
)
