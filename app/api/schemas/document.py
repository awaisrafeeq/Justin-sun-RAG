from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class DocumentUpload(BaseModel):
    """Schema for document upload request."""
    pass


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: UUID
    filename: str
    original_filename: str
    file_hash: str
    file_size: int
    mime_type: str
    status: str
    has_errors: bool
    error_message: Optional[str] = None
    extracted_text: Optional[str] = None
    doc_type: Optional[str] = None
    extracted_name: Optional[str] = None
    extracted_metadata: Optional[dict] = None
    table_count: int = 0
    image_count: int = 0
    page_count: int = 0
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    chunk_ids: Optional[bytes] = None
    
    class Config:
        from_attributes = True


class DocumentSummary(BaseModel):
    """Schema for document summary."""
    id: UUID
    filename: str
    original_filename: str
    status: str
    file_size: int
    doc_type: Optional[str] = None
    extracted_name: Optional[str] = None
    page_count: int = 0
    table_count: int = 0
    image_count: int = 0
    processed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentProcessingRequest(BaseModel):
    """Schema for document processing request."""
    extract_tables: bool = True
    extract_images: bool = True
    ocr_images: bool = True
    chunk_size: int = 1000
    chunk_overlap: int = 100


class DocumentChunk(BaseModel):
    """Schema for document chunk."""
    chunk_id: str
    chunk_index: int
    text: str
    page_number: Optional[int] = None
    chunk_type: str = "text"  # text, table, image
    metadata: dict = {}
    
    class Config:
        from_attributes = True


class DocumentProcessingResult(BaseModel):
    """Schema for document processing result."""
    document_id: UUID
    status: str
    page_count: int = 0
    text_length: int = 0
    table_count: int = 0
    image_count: int = 0
    chunk_count: int = 0
    processing_time: Optional[float] = None
    chunks: List[DocumentChunk] = []
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for document list response."""
    documents: List[DocumentSummary]
    total: int
    page: int = 1
    per_page: int = 20
    has_next: bool = False
    has_prev: bool = False
