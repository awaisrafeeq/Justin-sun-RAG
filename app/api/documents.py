from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.api.schemas.document import (
    DocumentResponse,
    DocumentSummary,
    DocumentProcessingRequest,
    DocumentProcessingResult,
    DocumentListResponse
)
from app.services.pdf_processor import PDFProcessor
from app.storage.models.document import Document
from workers.tasks import process_pdf_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    extract_tables: bool = Form(True),
    extract_images: bool = Form(True),
    ocr_images: bool = Form(True),
    reprocess_existing: bool = Form(False),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(100),
    db: AsyncSession = Depends(get_db)
):
    """Upload and process a PDF document."""
    
    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    if file.size > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    
    # Read file content
    file_content = await file.read()
    
    # Validate PDF format
    processor = PDFProcessor()
    is_valid, error_msg = processor.validate_pdf_file(file_content, file.filename)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Calculate file hash
    file_hash = processor.calculate_file_hash(file_content)
    
    # Check for duplicates
    existing_doc = await db.execute(
        select(Document).where(Document.file_hash == file_hash)
    )
    existing_document = existing_doc.scalar_one_or_none()
    if existing_document:
        if not reprocess_existing:
            raise HTTPException(
                status_code=409,
                detail="Document with this content already exists"
            )

        if existing_document.status == "processing":
            raise HTTPException(
                status_code=409,
                detail="Document is already being processed"
            )

        existing_document.status = "pending"
        existing_document.has_errors = False
        existing_document.error_message = None
        await db.commit()

        processing_options = {
            "extract_tables": extract_tables,
            "extract_images": extract_images,
            "ocr_images": ocr_images,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        }

        task = process_pdf_task.delay(
            document_id=str(existing_document.id),
            file_content=file_content,
            filename=existing_document.filename,
            original_filename=existing_document.original_filename,
            mime_type=existing_document.mime_type,
            processing_options=processing_options,
            reprocess=True,
        )
        logger.info(
            "Existing PDF %s re-queued for processing (task: %s)",
            existing_document.filename,
            task.id,
        )

        await db.refresh(existing_document)
        return existing_document
    
    # Create document record
    document = Document(
        filename=f"{uuid4().hex}.pdf",
        original_filename=file.filename,
        file_hash=file_hash,
        file_size=len(file_content),
        mime_type=file.content_type or "application/pdf"
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    # Queue for processing
    processing_options = {
        "extract_tables": extract_tables,
        "extract_images": extract_images,
        "ocr_images": ocr_images,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap
    }
    
    task = process_pdf_task.delay(
        document_id=str(document.id),
        file_content=file_content,
        filename=document.filename,
        original_filename=document.original_filename,
        mime_type=document.mime_type,
        processing_options=processing_options
    )
    
    logger.info(f"PDF {document.filename} queued for processing (task: {task.id})")
    
    return document


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List documents with pagination."""
    
    # Build query
    query = select(Document)
    count_query = select(func.count(Document.id))
    
    if status:
        query = query.where(Document.status == status)
        count_query = count_query.where(Document.status == status)
    
    # Get total count
    total = await db.scalar(count_query)
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(Document.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    documents = result.scalars().all()
    
    # Calculate pagination info
    has_next = offset + per_page < total
    has_prev = page > 1
    
    return DocumentListResponse(
        documents=[DocumentSummary.model_validate(doc) for doc in documents],
        total=total,
        page=page,
        per_page=per_page,
        has_next=has_next,
        has_prev=has_prev
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get document by ID."""
    
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.post("/{document_id}/process", response_model=DocumentProcessingResult)
async def process_document(
    document_id: UUID,
    processing_request: DocumentProcessingRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Re-process a document with different options."""
    
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Allow manual reset if stuck in processing for more than 5 minutes
    if document.status == "processing":
        # Check if it's been stuck for a while (allow manual override)
        if document.processed_at and (datetime.now(timezone.utc) - document.processed_at).total_seconds() > 300:
            # Stuck for over 5 minutes, allow reset
            logger.warning(f"Document {document_id} stuck in processing for over 5 minutes, allowing manual reset")
        else:
            raise HTTPException(
                status_code=409,
                detail="Document is already being processed"
            )
    
    # Reset document status
    document.status = "pending"
    document.has_errors = False
    document.error_message = None
    document.processed_at = None
    await db.commit()
    
    # Queue for processing
    processing_options = processing_request.model_dump()
    
    task = process_pdf_task.delay(
        document_id=str(document.id),
        file_content=None,  # Use existing file
        filename=document.filename,
        original_filename=document.original_filename,
        mime_type=document.mime_type,
        processing_options=processing_options,
        reprocess=True
    )
    
    logger.info(f"Document {document_id} re-queued for processing (task: {task.id})")
    
    return DocumentProcessingResult(
        document_id=document.id,
        status="queued",
        page_count=0,
        text_length=0,
        table_count=0,
        image_count=0,
        chunk_count=0
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a document."""
    
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete chunks from vector store
    if document.chunk_ids:
        try:
            from app.storage.vector_store import VectorStore
            vector_store = VectorStore()
            await vector_store.delete_episode_chunks(str(document.id))
        except Exception as e:
            logger.error(f"Failed to delete chunks for document {document_id}: {e}")
    
    # Delete document
    await db.delete(document)
    await db.commit()
    
    logger.info(f"Document {document_id} deleted")
    
    return {"message": "Document deleted successfully"}


@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get document chunks with pagination."""
    
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not document.chunk_ids:
        return {"chunks": [], "total": 0, "page": page, "per_page": per_page}
    
    # Get chunks from vector store
    try:
        from app.storage.vector_store import VectorStore
        vector_store = VectorStore()
        chunks = await vector_store.get_chunks_by_episode(str(document_id))
        
        # Apply pagination
        total = len(chunks)
        offset = (page - 1) * per_page
        paginated_chunks = chunks[offset:offset + per_page]
        
        return {
            "chunks": paginated_chunks,
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_next": offset + per_page < total,
            "has_prev": page > 1
        }
        
    except Exception as e:
        logger.error(f"Failed to get chunks for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chunks")


@router.get("/stats/summary")
async def get_documents_summary(db: AsyncSession = Depends(get_db)):
    """Get documents processing summary."""
    
    # Get total documents
    total_docs = await db.scalar(select(func.count(Document.id)))
    
    # Get documents by status
    status_counts = await db.execute(
        select(Document.status, func.count(Document.id))
        .group_by(Document.status)
    )
    
    status_summary = dict(status_counts.all())
    
    # Get processing statistics
    processed_docs = await db.scalar(
        select(func.count(Document.id))
        .where(Document.status == "completed")
    )
    
    total_pages = await db.scalar(
        select(func.sum(Document.page_count))
        .where(Document.status == "completed")
    ) or 0
    
    total_chunks = await db.scalar(
        select(func.count(Document.id))
        .where(Document.chunk_ids.isnot(None))
    ) or 0
    
    return {
        "total_documents": total_docs,
        "status_breakdown": status_summary,
        "processed_documents": processed_docs,
        "total_pages": total_pages,
        "documents_with_chunks": total_chunks,
        "processing_rate": (processed_docs / total_docs * 100) if total_docs > 0 else 0
    }
