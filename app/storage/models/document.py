from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from ..database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), unique=True, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending")
    has_errors = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    extracted_text = Column(Text, nullable=True)
    table_count = Column(Integer, default=0)
    image_count = Column(Integer, default=0)
    page_count = Column(Integer, default=0)
    title = Column(String(500), nullable=True)
    author = Column(String(255), nullable=True)
    subject = Column(String(500), nullable=True)
    creator = Column(String(255), nullable=True)
    producer = Column(String(255), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    chunk_ids = Column(LargeBinary, nullable=True)

    def __repr__(self) -> str:
        return f"<Document {self.filename} ({self.status})>"