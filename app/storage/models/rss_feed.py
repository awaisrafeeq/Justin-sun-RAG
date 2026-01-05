from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from ..database import Base

class RSSFeed(Base):
    __tablename__ = "rss_feeds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column("feed_url", String(1000), unique=True, nullable=False)
    title = Column("feed_title", String(500), nullable=True)
    description = Column("feed_description", Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<RSSFeed {self.title}>"