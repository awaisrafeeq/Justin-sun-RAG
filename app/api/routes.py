from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.api.schemas import FeedCreate, FeedResponse, FeedWithEpisodes, EpisodeResponse
from app.ingestion.audio_processor import AudioDownloadError, download_audio_to_tempfile
from app.ingestion.docling_client import get_docling_processor
from app.ingestion.rss_handler import ingest_feed
from app.storage.embeddings import EmbeddingClient
from app.storage.models import Episode, RSSFeed

router = APIRouter()


@router.get("/feeds")
async def list_feeds(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RSSFeed))
    return result.scalars().all()


@router.post("/feeds")
async def add_feed(payload: dict, db: AsyncSession = Depends(get_db)):
    try:
        feed, new_episodes = await ingest_feed(db, str(payload.get("url")))
        await db.commit()
        await db.refresh(feed)
        return feed
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/feeds/{feed_id}")
async def get_feed(feed_id: UUID, db: AsyncSession = Depends(get_db)):
    feed = await db.get(RSSFeed, feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    episodes = await db.execute(select(Episode).where(Episode.feed_id == feed_id).order_by(Episode.published_at.desc()))
    return {"feed": feed, "episodes": episodes.scalars().all()}


@router.post("/debug/docling/pdf")
async def debug_docling_pdf(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    suffix = Path(file.filename).suffix or ".pdf"
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            tmp.write(await file.read())

        processor = get_docling_processor()
        chunks = processor.process_pdf(tmp_path)

        preview = [
            {
                "chars": len(c.text or ""),
                "metadata": c.metadata,
            }
            for c in chunks[:3]
        ]
        return {"filename": file.filename, "chunks": len(chunks), "preview": preview}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


@router.post("/debug/docling/audio-url")
async def debug_docling_audio_url(audio_url: str = Form(...)):
    try:
        processor = get_docling_processor()
        with download_audio_to_tempfile(audio_url, suffix=Path(audio_url).suffix or ".audio") as audio_path:
            chunks = processor.process_audio_path(audio_path, source_url=audio_url)
    except AudioDownloadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    preview = [
        {
            "chars": len(c.text or ""),
            "metadata": c.metadata,
        }
        for c in chunks[:3]
    ]
    return {"audio_url": audio_url, "chunks": len(chunks), "preview": preview}


@router.post("/debug/embeddings/query")
async def debug_embeddings_query(query: str = Form(...)):
    client = EmbeddingClient()
    vector = await client.embed_query(query)
    return {"model": client.model, "dimensions": len(vector)}


@router.get("/feeds/{feed_id}/episodes", response_model=List[EpisodeResponse])
async def list_feed_episodes(feed_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Episode).where(Episode.feed_id == feed_id).order_by(Episode.published_at.desc()))
    episodes = result.scalars().all()
    if not episodes:
        # ensure feed exists
        exists = await db.get(RSSFeed, feed_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Feed not found")
    return episodes
