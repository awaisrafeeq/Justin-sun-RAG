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
from app.ingestion.chunker import TranscriptChunker
from app.ingestion.embedding_processor import EmbeddingProcessor
from app.storage.vector_store import VectorStore
from app.storage.models import Episode
from app.storage.database import AsyncSessionLocal

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
    """Process episode: download audio → transcribe → chunk → embed → store."""
    return _run_process_episode(episode_id)


def _run_process_episode(episode_id: str) -> dict:
    """Synchronous wrapper for async processing."""
    episode_uuid = uuid.UUID(episode_id)
    
    async def _run() -> dict:
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
                # Step 1: Download and transcribe audio
                processor = get_docling_processor()
                with download_audio_to_tempfile(episode.audio_url, suffix=Path(episode.audio_url).suffix or ".audio") as audio_path:
                    transcript_segments = processor.process_audio_path(audio_path, source_url=episode.audio_url)

                # Store transcript
                episode.transcript_segments = [
                    {
                        "text": segment.text,
                        "metadata": segment.metadata,
                    }
                    for segment in transcript_segments
                ]
                episode.transcript_text = "\n\n".join([segment.text for segment in transcript_segments if segment.text])
                await session.commit()

                # Step 2: Chunk transcript
                chunker = TranscriptChunker(max_chunk_size=1000, overlap=100, chunk_by="tokens")
                chunks = chunker.chunk_transcript(episode.transcript_segments)

                # Step 3: Generate embeddings
                embedding_processor = EmbeddingProcessor(batch_size=50)
                embeddings = await embedding_processor.process_chunks(chunks)

                # Step 4: Store in vector database
                vector_store = VectorStore()
                chunk_ids = await vector_store.store_chunks(
                    chunks=chunks,
                    embeddings=embeddings,
                    episode_id=episode_id,
                    metadata={
                        "episode_title": episode.title,
                        "feed_id": str(episode.feed_id),
                        "published_at": episode.published_at.isoformat() if episode.published_at else None
                    }
                )

                # Step 5: Update episode with chunk IDs
                episode.chunk_ids = chunk_ids
                episode.status = "completed"
                episode.processed_at = datetime.now(timezone.utc)
                episode.has_errors = False
                await session.commit()

                logger.info(
                    "Episode %s processed: %d transcript segments → %d chunks → %d embeddings stored",
                    episode_id, len(transcript_segments), len(chunks), len(chunk_ids)
                )
                return {
                    "episode_id": episode_id,
                    "transcript_segments": len(transcript_segments),
                    "chunks": len(chunks),
                    "embeddings": len(chunk_ids)
                }
            except Exception as e:
                # Update episode status to failed
                episode.status = "failed"
                episode.has_errors = True
                episode.processed_at = datetime.now(timezone.utc)
                await session.commit()
                
                logger.error(f"Episode {episode_id} processing failed: {e}")
                raise

    return asyncio.run(_run())
