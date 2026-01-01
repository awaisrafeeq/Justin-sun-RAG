#!/usr/bin/env python
"""Test using scroll method instead of query_points."""

import asyncio
from app.storage.vector_store import VectorStore
from app.services.query_embedding import QueryEmbeddingService

async def test_scroll_search():
    """Test search using scroll method with manual filtering."""
    store = VectorStore()
    await store.ensure_collection()
    
    # Get all points first
    all_points = store.client.scroll(
        collection_name='document_chunks',
        limit=10
    )
    
    if isinstance(all_points, tuple) and len(all_points) > 0:
        points = all_points[0]
        print(f"Total points in collection: {len(points)}")
        
        # Embed our query
        embedding_service = QueryEmbeddingService()
        query_embedding = await embedding_service.embed_query("50-day")
        
        # Manual similarity calculation (cosine similarity)
        best_matches = []
        for point in points:
            if hasattr(point, 'payload') and hasattr(point, 'vector'):
                point_text = point.payload.get('text', '')
                point_vector = point.vector
                
                if point_text and point_vector:
                    # Simple cosine similarity
                    dot_product = sum(a * b for a, b in zip(query_embedding, point_vector))
                    magnitude1 = sum(a * a for a in query_embedding) ** 0.5
                    magnitude2 = sum(b * b for b in point_vector) ** 0.5
                    
                    if magnitude1 > 0 and magnitude2 > 0:
                        similarity = dot_product / (magnitude1 * magnitude2)
                        
                        if similarity > 0.3:  # Low threshold
                            best_matches.append({
                                'text': point_text,
                                'similarity': similarity,
                                'id': point.id
                            })
        
        # Sort by similarity
        best_matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        print(f"\nBest matches for '50-day':")
        for i, match in enumerate(best_matches[:3]):
            print(f"{i+1}. Similarity: {match['similarity']:.3f}")
            print(f"   Text: {match['text'][:100]}...")
            print(f"   ID: {match['id']}")

if __name__ == "__main__":
    asyncio.run(test_scroll_search())
