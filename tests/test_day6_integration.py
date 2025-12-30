import pytest
import pytest_asyncio
import asyncio
from app.ingestion.chunker import TranscriptChunker, Chunk
from app.ingestion.embedding_processor import EmbeddingProcessor
from app.storage.vector_store import VectorStore


@pytest.mark.asyncio
async def test_end_to_end_chunking_and_embeddings():
    """Test the complete Day 6 pipeline: transcript → chunks → embeddings."""
    
    # Mock transcript segments (like from Docling)
    transcript_segments = [
        {
            "text": "Hello world. This is the first segment of our test transcript.",
            "metadata": {"timestamp": "00:00:00", "segment_index": 0}
        },
        {
            "text": "This is the second segment with more content to test chunking.",
            "metadata": {"timestamp": "00:01:00", "segment_index": 1}
        },
        {
            "text": "Final segment here. This should create multiple chunks when processed.",
            "metadata": {"timestamp": "00:02:00", "segment_index": 2}
        }
    ]
    
    # Step 1: Test chunking
    chunker = TranscriptChunker(max_chunk_size=50, overlap=10, chunk_by="tokens")
    chunks = chunker.chunk_transcript(transcript_segments)
    
    assert len(chunks) > 1, "Should create multiple chunks"
    
    # Verify chunks have proper metadata
    for chunk in chunks:
        assert isinstance(chunk, Chunk)
        assert chunk.text
        assert chunk.metadata is not None
        assert "chunk_index" in chunk.metadata
        assert "source_type" in chunk.metadata
        assert chunk.metadata["source_type"] == "podcast"
    
    # Step 2: Test embedding generation (mock)
    embedding_processor = EmbeddingProcessor(batch_size=2)
    
    # Mock the embedding client to avoid API calls
    import app.storage.embeddings
    original_embed_documents = app.storage.embeddings.EmbeddingClient.embed_documents
    
    async def mock_embed_documents(texts):
        # Return mock embeddings (1536 dimensions)
        return [[0.1] * 1536 for _ in texts]
    
    app.storage.embeddings.EmbeddingClient.embed_documents = mock_embed_documents
    
    try:
        embeddings = await embedding_processor.process_chunks(chunks)
        assert len(embeddings) == len(chunks), "Should have embedding for each chunk"
        
        for embedding in embeddings:
            assert len(embedding) == 1536, "Each embedding should be 1536 dimensions"
    
    finally:
        # Restore original method
        app.storage.embeddings.EmbeddingClient.embed_documents = original_embed_documents
    
    print(f"✅ Created {len(chunks)} chunks and {len(embeddings)} embeddings")


@pytest.mark.asyncio
async def test_vector_store_integration():
    """Test vector store operations."""
    
    # Mock chunks and embeddings
    chunks = [
        Chunk(text="Test chunk 1", metadata={"chunk_index": 0}),
        Chunk(text="Test chunk 2", metadata={"chunk_index": 1})
    ]
    
    embeddings = [
        [0.1] * 1536,
        [0.2] * 1536
    ]
    
    # Test vector store (mock to avoid Qdrant dependency)
    vector_store = VectorStore()
    
    # Mock the ensure_collection method to return a coroutine
    import asyncio
    
    async def mock_ensure_collection(vector_size):
        return None
    
    original_ensure_collection = vector_store.ensure_collection
    vector_store.ensure_collection = mock_ensure_collection
    
    # Mock the client upsert method
    original_upsert = vector_store.client.upsert
    upserted_points = []
    
    def mock_upsert(collection_name, points):
        upserted_points.extend(points)
    
    vector_store.client.upsert = mock_upsert
    
    try:
        chunk_ids = await vector_store.store_chunks(
            chunks=chunks,
            embeddings=embeddings,
            episode_id="test-episode-123",
            metadata={"test": True}
        )
        
        assert len(chunk_ids) == len(chunks), "Should return chunk ID for each chunk"
        assert len(upserted_points) == len(chunks), "Should upsert all points"
        
        # Verify point structure
        for point in upserted_points:
            assert hasattr(point, 'id')
            assert hasattr(point, 'vector')
            assert hasattr(point, 'payload')
            assert point.payload['episode_id'] == "test-episode-123"
            assert 'text' in point.payload
            assert 'chunk_index' in point.payload
    
    finally:
        # Restore original methods
        vector_store.ensure_collection = original_ensure_collection
        vector_store.client.upsert = original_upsert
    
    print(f"✅ Stored {len(chunks)} chunks in vector store")


def test_chunker_preserves_timestamps():
    """Test that chunking preserves timestamp metadata."""
    
    transcript_segments = [
        {
            "text": "First segment with timestamp.",
            "metadata": {"timestamp": "00:00:00", "segment_index": 0}
        },
        {
            "text": "Second segment with different timestamp.",
            "metadata": {"timestamp": "00:01:30", "segment_index": 1}
        }
    ]
    
    chunker = TranscriptChunker(max_chunk_size=100, overlap=20)
    chunks = chunker.chunk_transcript(transcript_segments)
    
    # At least some chunks should have timestamp info
    chunks_with_timestamps = [c for c in chunks if c.start_time is not None]
    assert len(chunks_with_timestamps) > 0, "Some chunks should preserve timestamps"
    
    # Verify metadata structure
    for chunk in chunks:
        assert "original_segment" in chunk.metadata, "Should reference original segment"
        original_segment = chunk.metadata["original_segment"]
        # Only check for timestamp if original_segment exists
        if original_segment is not None:
            # The timestamp is in the segment metadata, not the segment itself
            segment_metadata = original_segment.get("metadata", {})
            assert "timestamp" in segment_metadata, "Original segment should have timestamp"
    
    print(f"✅ Timestamps preserved in {len(chunks_with_timestamps)} out of {len(chunks)} chunks")


if __name__ == "__main__":
    # Run tests manually
    asyncio.run(test_end_to_end_chunking_and_embeddings())
    asyncio.run(test_vector_store_integration())
    test_chunker_preserves_timestamps()
    print("🎉 All Day 6 integration tests passed!")
