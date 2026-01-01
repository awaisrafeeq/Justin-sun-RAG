#!/usr/bin/env python
"""Debug the query_points response."""

import asyncio
from app.storage.vector_store import VectorStore
from app.services.query_embedding import QueryEmbeddingService

async def debug_query_points():
    """Debug query_points response."""
    store = VectorStore()
    await store.ensure_collection()
    
    # Embed our query
    embedding_service = QueryEmbeddingService()
    query_embedding = await embedding_service.embed_query("50-day")
    
    print(f"Query embedding length: {len(query_embedding)}")
    print(f"Query embedding first 5: {query_embedding[:5]}")
    
    # Call query_points directly
    search_result = store.client.query_points(
        collection_name='document_chunks',
        query=query_embedding,
        limit=3,
        with_vectors=True
    )
    
    print(f"Search result type: {type(search_result)}")
    print(f"Search result is tuple: {isinstance(search_result, tuple)}")
    
    if isinstance(search_result, tuple) and len(search_result) > 0:
        points = search_result[0]
        print(f"Points type: {type(points)}")
        print(f"Number of points: {len(points)}")
        
        for i, point in enumerate(points[:2]):  # Check first 2 points
            print(f"\n--- Point {i+1} ---")
            print(f"Type: {type(point)}")
            print(f"Has id: {hasattr(point, 'id')}")
            print(f"Has payload: {hasattr(point, 'payload')}")
            print(f"Has vector: {hasattr(point, 'vector')}")
            
            if hasattr(point, 'vector'):
                vector = point.vector
                print(f"Vector type: {type(vector)}")
                print(f"Vector length: {len(vector) if vector else 'None'}")
                print(f"Vector first 5: {vector[:5] if vector else 'None'}")
            else:
                print("Vector is None or missing")

if __name__ == "__main__":
    asyncio.run(debug_query_points())
