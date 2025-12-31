from __future__ import annotations

import hashlib
import logging
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from app.ingestion.docling_client import get_docling_processor
from app.ingestion.chunker import TranscriptChunker, Chunk
from app.ingestion.embedding_processor import EmbeddingProcessor
from app.storage.models.document import Document
from app.storage.vector_store import VectorStore
from app.api.schemas.document import DocumentProcessingResult, DocumentChunk

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Service for processing PDF documents."""
    
    def __init__(self):
        self.docling_processor = get_docling_processor()
        self.chunker = TranscriptChunker(max_chunk_size=1000, overlap=100, chunk_by="tokens")
        self.embedding_processor = EmbeddingProcessor(batch_size=50)
        self.vector_store = VectorStore()
    
    async def process_pdf(
        self,
        file_content: bytes,
        filename: str,
        original_filename: str,
        mime_type: str,
        processing_options: Optional[Dict[str, Any]] = None
    ) -> DocumentProcessingResult:
        """
        Process PDF document end-to-end.
        
        Args:
            file_content: PDF file content
            filename: Generated filename
            original_filename: Original filename from upload
            mime_type: MIME type of file
            processing_options: Processing configuration options
            
        Returns:
            DocumentProcessingResult with chunks and metadata
        """
        import time
        start_time = time.time()
        
        # Default processing options
        options = {
            "extract_tables": True,
            "extract_images": True,
            "ocr_images": True,
            "chunk_size": 1000,
            "chunk_overlap": 100
        }
        if processing_options:
            options.update(processing_options)
        
        try:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
            
            try:
                # Process with Docling
                logger.info(f"Processing PDF: {filename}")
                try:
                    chunks = self.docling_processor.process_pdf(Path(tmp_file_path))
                except Exception as e:
                    extracted_text = self._extract_text_fallback(file_content)
                    if not extracted_text:
                        raise
                    logger.warning(
                        "Docling failed (%s). Falling back to pypdf text extraction for %s",
                        e,
                        filename,
                    )
                    text_chunks = self._chunk_plain_text(extracted_text, options)
                    embeddings = await self.embedding_processor.process_chunks(text_chunks)
                    chunk_ids = await self.vector_store.store_chunks(
                        chunks=text_chunks,
                        embeddings=embeddings,
                        episode_id=str(UUID(int=0)),
                        metadata={
                            "document_type": "pdf",
                            "filename": filename,
                            "original_filename": original_filename,
                            "page_count": 0,
                            "table_count": 0,
                            "image_count": 0,
                            "has_text": True,
                            "has_tables": False,
                            "has_images": False,
                            "extraction_method": "pypdf_fallback",
                        },
                    )

                    processing_time = time.time() - start_time
                    result = DocumentProcessingResult(
                        document_id=UUID(int=0),
                        status="completed",
                        page_count=0,
                        text_length=len(extracted_text),
                        table_count=0,
                        image_count=0,
                        chunk_count=len(text_chunks),
                        processing_time=processing_time,
                        chunks=[
                            DocumentChunk(
                                chunk_id=chunk_ids[i],
                                chunk_index=i,
                                text=text_chunks[i].text,
                                page_number=text_chunks[i].metadata.get("page_number"),
                                chunk_type=text_chunks[i].metadata.get("chunk_type", "text"),
                                metadata=text_chunks[i].metadata,
                            )
                            for i in range(len(text_chunks))
                        ],
                    )
                    logger.info(
                        "PDF processing complete via fallback: %d chunks, %.2fs",
                        len(text_chunks),
                        processing_time,
                    )
                    return result
                
                # Extract metadata
                metadata = self._extract_pdf_metadata(chunks)
                
                # Create text chunks
                text_chunks = self._create_text_chunks(chunks, options)
                
                # Generate embeddings
                embeddings = await self.embedding_processor.process_chunks(text_chunks)
                
                # Store in vector database
                chunk_ids = await self.vector_store.store_chunks(
                    chunks=text_chunks,
                    embeddings=embeddings,
                    episode_id=str(UUID(int=0)),  # Use dummy episode_id for documents
                    metadata={
                        "document_type": "pdf",
                        "filename": filename,
                        "original_filename": original_filename,
                        **metadata
                    }
                )
                
                processing_time = time.time() - start_time
                
                # Create result
                result = DocumentProcessingResult(
                    document_id=UUID(int=0),  # Will be set by caller
                    status="completed",
                    page_count=metadata.get("page_count", 0),
                    text_length=len(" ".join([chunk.text for chunk in text_chunks])),
                    table_count=metadata.get("table_count", 0),
                    image_count=metadata.get("image_count", 0),
                    chunk_count=len(text_chunks),
                    processing_time=processing_time,
                    chunks=[
                        DocumentChunk(
                            chunk_id=chunk_ids[i],
                            chunk_index=i,
                            text=text_chunks[i].text,
                            page_number=text_chunks[i].metadata.get("page_number"),
                            chunk_type=text_chunks[i].metadata.get("chunk_type", "text"),
                            metadata=text_chunks[i].metadata
                        )
                        for i in range(len(text_chunks))
                    ]
                )
                
                logger.info(f"PDF processing complete: {len(text_chunks)} chunks, {processing_time:.2f}s")
                return result
                
            finally:
                # Clean up temporary file
                tmp_path = Path(tmp_file_path)
                for attempt in range(6):
                    try:
                        tmp_path.unlink(missing_ok=True)
                        break
                    except PermissionError as e:
                        if attempt == 5:
                            logger.warning("Failed to delete temp PDF %s due to file lock: %s", tmp_path, e)
                            break
                        time.sleep(0.2 * (attempt + 1))
                
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            raise
    
    def _extract_pdf_metadata(self, chunks: List[Any]) -> Dict[str, Any]:
        """Extract metadata from processed chunks."""
        metadata = {
            "page_count": 0,
            "table_count": 0,
            "image_count": 0,
            "has_text": False,
            "has_tables": False,
            "has_images": False
        }
        
        page_numbers = set()
        
        for chunk in chunks:
            # Count page numbers
            if hasattr(chunk, 'page_number') and chunk.page_number:
                page_numbers.add(chunk.page_number)
            
            # Count content types
            if hasattr(chunk, 'type'):
                if chunk.type == 'table':
                    metadata["table_count"] += 1
                    metadata["has_tables"] = True
                elif chunk.type == 'image':
                    metadata["image_count"] += 1
                    metadata["has_images"] = True
                elif chunk.type == 'text':
                    metadata["has_text"] = True
        
        metadata["page_count"] = len(page_numbers)
        return metadata
    
    def _create_text_chunks(self, docling_chunks: List[Any], options: Dict[str, Any]) -> List[Chunk]:
        """Create text chunks from Docling output."""
        text_chunks = []
        
        for i, docling_chunk in enumerate(docling_chunks):
            # Convert Docling chunk to our Chunk format
            chunk_text = ""
            chunk_metadata = {
                "chunk_index": i,
                "chunk_type": "text",
                "page_number": None
            }
            
            # Extract text based on chunk type
            if hasattr(docling_chunk, 'text'):
                chunk_text = docling_chunk.text
            elif hasattr(docling_chunk, 'content'):
                chunk_text = str(docling_chunk.content)
            else:
                chunk_text = str(docling_chunk)
            
            # Extract metadata
            if hasattr(docling_chunk, 'page_number'):
                chunk_metadata["page_number"] = docling_chunk.page_number
            
            if hasattr(docling_chunk, 'type'):
                chunk_metadata["chunk_type"] = docling_chunk.type
            
            # Only add non-empty chunks
            if chunk_text.strip():
                text_chunks.append(Chunk(
                    text=chunk_text,
                    metadata=chunk_metadata
                ))
        
        return text_chunks

    def _extract_text_fallback(self, file_content: bytes) -> str:
        try:
            from pypdf import PdfReader
        except Exception:
            return ""

        try:
            import io

            reader = PdfReader(io.BytesIO(file_content))
            pages_text = []
            for page in reader.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    pages_text.append(page_text)
            return "\n\n".join(pages_text).strip()
        except Exception:
            return ""

    def _chunk_plain_text(self, text: str, options: Dict[str, Any]) -> List[Chunk]:
        chunk_size = int(options.get("chunk_size", 1000))
        chunk_overlap = int(options.get("chunk_overlap", 100))

        if not text:
            return []

        approx_chars = max(chunk_size * 4, 1)
        overlap_chars = max(chunk_overlap, 0)

        chunks: List[Chunk] = []
        start = 0
        idx = 0
        while start < len(text):
            end = min(start + approx_chars, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        metadata={
                            "chunk_index": idx,
                            "chunk_type": "text",
                            "page_number": None,
                        },
                    )
                )
                idx += 1
            if end >= len(text):
                break
            start = max(end - overlap_chars, start + 1)
        return chunks
    
    @staticmethod
    def calculate_file_hash(file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()
    
    @staticmethod
    def validate_pdf_file(file_content: bytes, filename: str) -> Tuple[bool, str]:
        """Validate PDF file."""
        # Check file size (max 50MB)
        if len(file_content) > 50 * 1024 * 1024:
            return False, "File too large (max 50MB)"
        
        # Check file extension
        if not filename.lower().endswith('.pdf'):
            return False, "File must be a PDF"
        
        # Check PDF header
        if not file_content.startswith(b'%PDF'):
            return False, "Invalid PDF file format"
        
        return True, "Valid PDF file"
