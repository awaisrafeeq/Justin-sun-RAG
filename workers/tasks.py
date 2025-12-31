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
from app.storage.models.document import Document
from app.storage.database import AsyncSessionLocal
from app.services.pdf_processor import PDFProcessor
from app.services.document_metadata import DocumentMetadataService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="workers.tasks.process_pdf",
    autoretry_for=(),
)
def process_pdf_task(
    self,
    document_id: str,
    file_content: bytes = None,
    filename: str = None,
    original_filename: str = None,
    mime_type: str = None,
    processing_options: dict = None,
    reprocess: bool = False
) -> dict:
    """Process PDF document with Docling and store in vector database."""
    return _run_process_pdf(
        document_id, file_content, filename, original_filename, 
        mime_type, processing_options, reprocess
    )


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


def _run_process_pdf(
    document_id: str,
    file_content: bytes = None,
    filename: str = None,
    original_filename: str = None,
    mime_type: str = None,
    processing_options: dict = None,
    reprocess: bool = False
) -> dict:
    """Synchronous wrapper for PDF processing."""
    document_uuid = uuid.UUID(document_id)
    
    async def _run() -> dict:
        async with AsyncSessionLocal() as session:
            document = await session.get(Document, document_uuid)
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # Update status to processing
            document.status = "processing"
            document.has_errors = False
            document.error_message = None
            await session.commit()
            
            try:
                # Get file content if not provided (reprocessing)
                if not file_content and not reprocess:
                    raise ValueError("File content is required for new documents")

                # Reprocess mode may not have access to original PDF bytes.
                # If we already have extracted_text, we can still run Day 9 metadata extraction.
                if reprocess and not file_content and document.extracted_text:
                    metadata_service = DocumentMetadataService()
                    meta_result = await metadata_service.classify_and_extract(
                        text=document.extracted_text,
                        filename=document.original_filename,
                    )
                    document.doc_type = meta_result.doc_type
                    document.extracted_name = meta_result.extracted_name
                    document.extracted_metadata = meta_result.extracted_metadata
                    document.status = "completed"
                    document.processed_at = datetime.now(timezone.utc)
                    await session.commit()

                    logger.info(
                        "Document %s metadata re-extracted (no PDF bytes available)",
                        document_id,
                    )

                    return {
                        "document_id": document_id,
                        "status": "completed",
                        "page_count": document.page_count or 0,
                        "chunk_count": 0,
                        "table_count": document.table_count or 0,
                        "image_count": document.image_count or 0,
                        "processing_time": 0,
                    }

                # If reprocessing and we have neither the original bytes nor extracted text,
                # we cannot proceed. Fail the job without triggering Celery autoretry loops.
                if reprocess and not file_content and not document.extracted_text:
                    document.status = "failed"
                    document.has_errors = True
                    document.error_message = (
                        "Cannot reprocess: no stored PDF bytes available and extracted_text is empty. "
                        "Re-upload the PDF with reprocess_existing=true to re-queue using fresh bytes."
                    )
                    document.processed_at = datetime.now(timezone.utc)
                    await session.commit()
                    logger.error(
                        "Document %s reprocess failed: missing bytes and extracted_text",
                        document_id,
                    )
                    return {
                        "document_id": document_id,
                        "status": "failed",
                        "page_count": 0,
                        "chunk_count": 0,
                        "table_count": 0,
                        "image_count": 0,
                        "processing_time": 0,
                    }

                # Initialize processor
                processor = PDFProcessor()
                
                # Process PDF
                result = await processor.process_pdf(
                    file_content=file_content,
                    filename=filename or document.filename,
                    original_filename=original_filename or document.original_filename,
                    mime_type=mime_type or document.mime_type,
                    processing_options=processing_options
                )
                
                # Update document with results
                document.status = "completed"
                document.processed_at = datetime.now(timezone.utc)
                document.page_count = result.page_count
                document.table_count = result.table_count
                document.image_count = result.image_count
                chunk_ids = getattr(result, 'chunk_ids', None)
                if isinstance(chunk_ids, list):
                    import json
                    document.chunk_ids = json.dumps(chunk_ids).encode('utf-8')
                else:
                    document.chunk_ids = chunk_ids or b""
                
                # Extract text from chunks
                if result.chunks:
                    document.extracted_text = " ".join([chunk.text for chunk in result.chunks])

                if document.extracted_text:
                    metadata_service = DocumentMetadataService()
                    meta_result = await metadata_service.classify_and_extract(
                        text=document.extracted_text,
                        filename=document.original_filename,
                    )
                    document.doc_type = meta_result.doc_type
                    document.extracted_name = meta_result.extracted_name
                    document.extracted_metadata = meta_result.extracted_metadata

                await session.commit()
                
                logger.info(
                    "Document %s processed: %d pages, %d chunks, %d tables, %d images",
                    document_id, result.page_count, result.chunk_count, 
                    result.table_count, result.image_count
                )
                
                return {
                    "document_id": document_id,
                    "status": "completed",
                    "page_count": result.page_count,
                    "chunk_count": result.chunk_count,
                    "table_count": result.table_count,
                    "image_count": result.image_count,
                    "processing_time": result.processing_time
                }
                
            except Exception as e:
                # Update document status to failed
                document.status = "failed"
                document.has_errors = True
                document.error_message = str(e)
                document.processed_at = datetime.now(timezone.utc)
                await session.commit()
                
                logger.error(f"Document {document_id} processing failed: {e}")
                raise
    
    return asyncio.run(_run())


def _run_process_episode(episode_id: str) -> dict:
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
