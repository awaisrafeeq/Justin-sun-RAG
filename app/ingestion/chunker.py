from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """A chunk of transcript text with metadata."""
    text: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    segment_index: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class TranscriptChunker:
    """
    Chunk transcript text while preserving timestamps and metadata.
    Supports both token-based and character-based chunking with overlap.
    """
    
    def __init__(
        self,
        max_chunk_size: int = 1000,
        overlap: int = 100,
        chunk_by: str = "tokens",  # "tokens" or "characters"
    ):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.chunk_by = chunk_by
        
    def chunk_transcript(self, transcript_segments: List[Dict[str, Any]]) -> List[Chunk]:
        """
        Chunk transcript segments while preserving timestamps.
        
        Args:
            transcript_segments: List of transcript segments from Docling
            
        Returns:
            List of chunks with preserved metadata
        """
        if not transcript_segments:
            return []
            
        # First, extract text and combine segments
        combined_text = "\n\n".join([
            segment.get("text", "") for segment in transcript_segments if segment.get("text")
        ])
        
        logger.info(
            "Chunking transcript: %d segments, %d characters",
            len(transcript_segments),
            len(combined_text)
        )
        
        # Create chunks based on the chosen method
        if self.chunk_by == "tokens":
            chunks = self._chunk_by_tokens(combined_text)
        else:
            chunks = self._chunk_by_characters(combined_text)
            
        # Map chunks back to original segments for timestamps
        chunks_with_metadata = self._add_metadata_to_chunks(
            chunks, transcript_segments
        )
        
        logger.info("Created %d chunks", len(chunks_with_metadata))
        return chunks_with_metadata
    
    def _chunk_by_tokens(self, text: str) -> List[str]:
        """
        Split text into chunks by approximate token count.
        Using a simple heuristic: ~1 token per 4 characters for English.
        """
        if not text:
            return []
            
        chunks = []
        start = 0
        
        while start < len(text):
            # Calculate end position based on token limit
            end = min(start + self.max_chunk_size * 4, len(text))
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings near the target end
                sentence_end = self._find_sentence_boundary(text, start, end)
                if sentence_end > start:
                    end = sentence_end
            
            chunks.append(text[start:end].strip())
            
            # Calculate next start with overlap
            start = max(end - self.overlap, start + 1)
            
        return [chunk for chunk in chunks if chunk]
    
    def _chunk_by_characters(self, text: str) -> List[str]:
        """
        Split text into chunks by character count.
        """
        if not text:
            return []
            
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + self.max_chunk_size, len(text))
            
            # Try to break at sentence boundary
            if end < len(text):
                sentence_end = self._find_sentence_boundary(text, start, end)
                if sentence_end > start:
                    end = sentence_end
            
            chunks.append(text[start:end].strip())
            
            # Calculate next start with overlap
            start = max(end - self.overlap, start + 1)
            
        return [chunk for chunk in chunks if chunk]
    
    def _find_sentence_boundary(self, text: str, start: int, end: int) -> int:
        """
        Find the best sentence boundary between start and end.
        """
        # Look for sentence endings in the last 200 characters of the chunk
        search_start = max(start, end - 200)
        search_text = text[search_start:end]
        
        # Pattern to match sentence endings
        sentence_pattern = r'[.!?]+\s+["\'"")]*'
        matches = list(re.finditer(sentence_pattern, search_text))
        
        if matches:
            # Return the position of the last sentence ending
            last_match = matches[-1]
            return search_start + last_match.end()
        
        # If no sentence boundary found, try to break at word boundary
        word_pattern = r'\s+\S+'
        word_matches = list(re.finditer(word_pattern, search_text))
        
        if word_matches:
            last_word = word_matches[-1]
            return search_start + last_word.start()
        
        # Fallback to the original end
        return end
    
    def _add_metadata_to_chunks(
        self, 
        chunks: List[str], 
        transcript_segments: List[Dict[str, Any]]
    ) -> List[Chunk]:
        """
        Add timestamp and segment metadata to chunks.
        """
        result = []
        
        for i, chunk_text in enumerate(chunks):
            # Find the most relevant segment for this chunk
            segment_index = self._find_relevant_segment(
                chunk_text, transcript_segments
            )
            
            if segment_index is not None:
                segment = transcript_segments[segment_index]
                metadata = segment.get("metadata", {})
                
                chunk = Chunk(
                    text=chunk_text,
                    start_time=metadata.get("timestamp"),
                    segment_index=segment_index,
                    metadata={
                        "chunk_index": i,
                        "source_type": "podcast",
                        "original_segment": segment,
                        **metadata
                    }
                )
            else:
                # Still add basic metadata for chunks without segment mapping
                chunk = Chunk(
                    text=chunk_text,
                    segment_index=None,
                    metadata={
                        "chunk_index": i,
                        "source_type": "podcast",
                        "original_segment": None  # Explicitly set to None
                    }
                )
            
            result.append(chunk)
        
        return result
    
    def _find_relevant_segment(
        self, 
        chunk_text: str, 
        transcript_segments: List[Dict[str, Any]]
    ) -> Optional[int]:
        """
        Find the most relevant transcript segment for a chunk.
        Uses simple text overlap heuristic.
        """
        if not transcript_segments:
            return None
            
        best_segment = None
        best_score = 0
        
        for i, segment in enumerate(transcript_segments):
            segment_text = segment.get("text", "")
            
            # Simple overlap score
            overlap = len(set(chunk_text.lower().split()) & 
                        set(segment_text.lower().split()))
            score = overlap / max(len(chunk_text.split()), 1)
            
            if score > best_score:
                best_score = score
                best_segment = i
        
        return best_segment if best_score >= 0 else None
