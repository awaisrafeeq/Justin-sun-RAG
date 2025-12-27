from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class FeedCreate(BaseModel):
    url: HttpUrl


class FeedResponse(BaseModel):
    id: UUID
    feed_url: HttpUrl
    feed_title: Optional[str] = None
    feed_description: Optional[str] = None
    total_episodes: int
    last_fetched_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EpisodeResponse(BaseModel):
    id: UUID
    guid: str
    title: Optional[str]
    audio_url: Optional[str]
    published_at: Optional[datetime]
    status: str

    class Config:
        from_attributes = True


class FeedWithEpisodes(BaseModel):
    feed: FeedResponse
    episodes: List[EpisodeResponse]
