from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from celery import shared_task

from app.ingestion.audio_processor import AudioDownloadError, download_audio_to_tempfile
from app.ingestion.docling_client import get_docling_processor
from app.storage.database import AsyncSessionLocal
from app.storage.models import Episode

logger = logging.getLogger(__name__)


@shared_task(name="workers.tasks.process_pdf")
def process_pdf_task(file_path: str) -> dict:
    """
    Convert a PDF into chunks via Docling and return summary stats.
    """
    processor = get_docling_processor()
    chunks = processor.process_pdf(Path(file_path))
    logger.info("Processed PDF %s into %s chunks", file_path, len(chunks))
    return {"filename": Path(file_path).name, "chunks": len(chunks)}


@shared_task(
    bind=True,
    name="workers.tasks.process_episode",
    autoretry_for=(AudioDownloadError, httpx.HTTPError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_episode_task(self, episode_id: str) -> dict:
    """
    Download podcast audio, run Docling transcription, update episode status.
    """

    async def _run() -> dict:
        episode_uuid = uuid.UUID(episode_id)
        async with AsyncSessionLocal() as session:
            episode = await session.get(Episode, episode_uuid)
            if not episode:
                raise ValueError(f"Episode {episode_id} not found")
            if not episode.audio_url:
                raise ValueError(f"Episode {episode_id} missing audio_url")

            episode.status = "processing"
            episode.has_errors = False
            await session.commit()

            try:
                processor = get_docling_processor()
                with download_audio_to_tempfile(episode.audio_url, suffix=Path(episode.audio_url).suffix or ".audio") as audio_path:
                    chunks = processor.process_audio_path(audio_path, source_url=episode.audio_url)

                episode.transcript_segments = [
                    {
                        "text": c.text,
                        "metadata": c.metadata,
                    }
                    for c in chunks
                ]
                episode.transcript_text = "\n\n".join([c.text for c in chunks if c.text])
                episode.status = "completed"
                episode.processed_at = datetime.now(timezone.utc)
                episode.has_errors = False
                await session.commit()

                logger.info("Episode %s transcribed into %s chunks", episode_id, len(chunks))
                return {"episode_id": episode_id, "chunks": len(chunks)}
            except Exception:
                episode.status = "failed"
                episode.has_errors = True
                episode.processed_at = datetime.now(timezone.utc)
                await session.commit()
                raise

    return asyncio.run(_run())
