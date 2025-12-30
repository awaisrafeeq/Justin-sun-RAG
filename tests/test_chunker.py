import pytest
from app.ingestion.chunker import TranscriptChunker, Chunk


def test_sliding_window_chunk_respects_overlap():
    """Test that chunking respects overlap parameter."""
    chunker = TranscriptChunker(max_chunk_size=100, overlap=20, chunk_by="characters")
    
    text = "A " * 50 + "B " * 50 + "C " * 50
    chunks = chunker._chunk_by_characters(text)
    
    assert len(chunks) > 1
    
    # Check that chunks overlap
    first_chunk = chunks[0]
    second_chunk = chunks[1]
    
    # The end of first chunk should appear in second chunk (overlap)
    overlap_text = first_chunk[-20:] if len(first_chunk) >= 20 else first_chunk
    assert overlap_text in second_chunk


def test_chunk_from_docling_sections_builds_payload():
    """Test chunking from Docling transcript segments."""
    chunker = TranscriptChunker(max_chunk_size=200, overlap=50)
    
    # Mock transcript segments like Docling output
    segments = [
        {
            "text": "Hello world. This is the first segment.",
            "metadata": {"timestamp": "00:00:00", "segment_index": 0}
        },
        {
            "text": "This is the second segment with more content.",
            "metadata": {"timestamp": "00:01:00", "segment_index": 1}
        },
        {
            "text": "Final segment here.",
            "metadata": {"timestamp": "00:02:00", "segment_index": 2}
        }
    ]
    
    chunks = chunker.chunk_transcript(segments)
    
    assert len(chunks) > 0
    
    # Check that chunks have proper metadata
    for chunk in chunks:
        assert isinstance(chunk, Chunk)
        assert chunk.text
        assert chunk.metadata is not None
        assert "chunk_index" in chunk.metadata
        assert "source_type" in chunk.metadata
        assert chunk.metadata["source_type"] == "podcast"


def test_token_based_chunking():
    """Test token-based chunking."""
    chunker = TranscriptChunker(max_chunk_size=10, overlap=2, chunk_by="tokens")
    
    text = "This is a test sentence. This is another test sentence."
    chunks = chunker._chunk_by_tokens(text)
    
    assert len(chunks) > 1
    
    # Check that chunks are not empty
    for chunk in chunks:
        assert chunk.strip()
        assert len(chunk.split()) <= 12  # Allow some flexibility


def test_empty_transcript():
    """Test handling of empty transcript."""
    chunker = TranscriptChunker()
    
    # Empty list
    chunks = chunker.chunk_transcript([])
    assert chunks == []
    
    # List with empty segments
    chunks = chunker.chunk_transcript([{"text": ""}, {"text": ""}])
    assert chunks == []


def test_sentence_boundary_detection():
    """Test finding sentence boundaries."""
    chunker = TranscriptChunker()
    
    text = "This is sentence one. This is sentence two! This is sentence three?"
    
    # Test finding boundary within the text
    boundary = chunker._find_sentence_boundary(text, 0, len(text))
    
    # Should find a sentence ending
    assert boundary > 0
    assert boundary <= len(text)
    
    # Check that boundary is at a sentence ending
    text_up_to_boundary = text[:boundary]
    assert text_up_to_boundary.rstrip().endswith(('.', '!', '?'))
