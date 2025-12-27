from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.api.schemas import EpisodeResponse, FeedCreate, FeedResponse, FeedWithEpisodes
from app.ingestion.rss_handler import ingest_feed
from app.storage.models import Episode, RSSFeed

router = APIRouter()


@router.get("/feeds", response_model=List[FeedResponse])
async def list_feeds(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RSSFeed))
    return result.scalars().all()


@router.post("/feeds", response_model=FeedResponse, status_code=status.HTTP_201_CREATED)
async def add_feed(payload: FeedCreate, db: AsyncSession = Depends(get_db)):
    feed, new_episodes = await ingest_feed(db, str(payload.url))
    await db.commit()
    await db.refresh(feed)
    return feed


@router.get("/feeds/{feed_id}", response_model=FeedWithEpisodes)
async def get_feed(feed_id: UUID, db: AsyncSession = Depends(get_db)):
    feed = await db.get(RSSFeed, feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    episodes = await db.execute(select(Episode).where(Episode.feed_id == feed_id).order_by(Episode.published_at.desc()))
    return FeedWithEpisodes(feed=feed, episodes=episodes.scalars().all())


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
