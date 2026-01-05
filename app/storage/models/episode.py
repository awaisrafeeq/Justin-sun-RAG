from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from ..database import Base

class Episode(Base):
    __tablename__ = "episodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guid = Column(String(500), nullable=True)
    title = Column(String(500), nullable=False)
    audio_url = Column(String(1000), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="pending")
    feed_id = Column(UUID(as_uuid=True), ForeignKey("rss_feeds.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Episode {self.title}>"