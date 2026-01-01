#!/usr/bin/env python
"""Debug QueryResponse structure."""

import asyncio
from app.storage.vector_store import VectorStore
from app.services.query_embedding import QueryEmbeddingService

async def debug_query_response():
    """Debug QueryResponse object structure."""
    store = VectorStore()
    await store.ensure_collection()
    
    # Embed our query
    embedding_service = QueryEmbeddingService()
    query_embedding = await embedding_service.embed_query("50-day")
    
    # Call query_points directly
    search_result = store.client.query_points(
        collection_name='document_chunks',
        query=query_embedding,
        limit=3,
        with_vectors=True
    )
    
    print(f"Search result type: {type(search_result)}")
    print(f"QueryResponse attributes: {[attr for attr in dir(search_result) if not attr.startswith('_')]}")
    
    # Try to access common attributes
    for attr in ['points', 'result', 'data']:
        if hasattr(search_result, attr):
            try:
                value = getattr(search_result, attr)
                print(f"{attr}: {type(value)} - {str(value)[:100] if value else 'None'}")
            except Exception as e:
                print(f"{attr}: Error - {e}")

if __name__ == "__main__":
    asyncio.run(debug_query_response())
