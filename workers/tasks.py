from __future__ import annotations

import logging
from pathlib import Path

from celery import shared_task

from app.ingestion.docling_client import get_docling_processor
from app.storage.embeddings import EmbeddingClient

logger = logging.getLogger(__name__)


@shared_task(name="workers.tasks.process_pdf")
def process_pdf_task(file_path: str) -> dict:
    """
    Placeholder task: convert a PDF into chunks via Docling and return summary stats.
    """
    processor = get_docling_processor()
    chunks = processor.process_pdf(Path(file_path))
    logger.info("Processed PDF %s into %s chunks", file_path, len(chunks))
    return {"filename": Path(file_path).name, "chunks": len(chunks)}


@shared_task(name="workers.tasks.process_audio")
def process_audio_task(audio_bytes: bytes, source_url: str | None = None) -> dict:
    """
    Placeholder task for audio ingestion. In production this would fetch the audio first.
    """
    processor = get_docling_processor()
    chunks = processor.process_audio(audio_bytes, source_url=source_url)
    logger.info("Processed audio %s into %s segments", source_url, len(chunks))
    return {"source_url": source_url, "chunks": len(chunks)}


@shared_task(name="workers.tasks.embed_chunks")
def embed_chunks_task(text_chunks: list[str]) -> dict:
    """
    Example Celery task for embedding text asynchronously.
    """
    embedding_client = EmbeddingClient()

    async def _embed() -> list[list[float]]:
        return await embedding_client.embed_documents(text_chunks)

    import asyncio

    vectors = asyncio.run(_embed())
    logger.info("Embedded %s chunks", len(text_chunks))
    return {"count": len(vectors)}
