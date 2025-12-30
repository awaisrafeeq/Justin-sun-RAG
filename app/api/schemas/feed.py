from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, HttpUrl

class FeedCreate(BaseModel):
    url: HttpUrl

class FeedResponse(BaseModel):
    id: UUID
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    last_fetched: Optional[datetime] = None
    status: str = "active"
    
    class Config:
        from_attributes = True

class EpisodeResponse(BaseModel):
    id: UUID
    title: Optional[str]
    description: Optional[str] = None
    audio_url: Optional[str]
    published_at: Optional[datetime]
    status: str
    
    class Config:
        from_attributes = True

class FeedWithEpisodes(BaseModel):
    feed: FeedResponse
    episodes: List[EpisodeResponse]
