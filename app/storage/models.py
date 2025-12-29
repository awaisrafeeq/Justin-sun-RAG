from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class RSSFeed(Base, TimestampMixin):
    __tablename__ = "rss_feeds"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    feed_url: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    feed_title: Mapped[Optional[str]] = mapped_column(String(512))
    feed_description: Mapped[Optional[str]] = mapped_column(Text)
    last_fetched_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True)
    )
    total_episodes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    episodes: Mapped[List["Episode"]] = relationship(
        back_populates="feed", cascade="all, delete-orphan"
    )


class Episode(Base, TimestampMixin):
    __tablename__ = "episodes"
    __table_args__ = (
        UniqueConstraint("feed_id", "guid", name="uq_feed_guid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    feed_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rss_feeds.id", ondelete="CASCADE"), nullable=False
    )
    guid: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(512))
    audio_url: Mapped[Optional[str]] = mapped_column(String(1024))
    published_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    status: Mapped[str] = mapped_column(
        String(32), default="pending", nullable=False
    )  # pending/processing/completed/failed
    transcript_text: Mapped[Optional[str]] = mapped_column(Text)
    transcript_segments: Mapped[Optional[dict]] = mapped_column(JSON)
    chunk_ids: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    processed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    has_errors: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    feed: Mapped[RSSFeed] = relationship(back_populates="episodes")


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    doc_type: Mapped[str] = mapped_column(String(64), nullable=False)
    extracted_name: Mapped[Optional[str]] = mapped_column(String(256))
    extracted_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    chunk_ids: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
