#!/usr/bin/env python
"""Check what's in Qdrant collection."""

import asyncio
from app.storage.vector_store import VectorStore

async def check_qdrant_content():
    """Check actual content in Qdrant."""
    store = VectorStore()
    await store.ensure_collection()
    
    # Get collection info
    collection_info = store.client.get_collection('document_chunks')
    print(f"Collection points count: {collection_info.points_count}")
    
    # Get all points
    result = store.client.scroll(
        collection_name='document_chunks',
        limit=10
    )
    
    if isinstance(result, tuple) and len(result) > 0:
        points = result[0]
        print(f"Found {len(points)} points")
        
        for i, point in enumerate(points[:3]):  # Show first 3
            if isinstance(point, list) and len(point) >= 3:
                point_id = point[0]
                point_payload = point[2]
                print(f"\n--- Point {i+1} ---")
                print(f"ID: {point_id}")
                text_preview = point_payload.get('text', '')[:200]
                print(f"Text preview: {text_preview}")
                print(f"Document ID: {point_payload.get('document_id', '')}")
                print(f"Metadata keys: {list(point_payload.keys())}")
                print(f"Has text: {'Yes' if point_payload.get('text') else 'No'}")
                print(f"Text length: {len(point_payload.get('text', ''))}")
            else:
                print(f"Point {i}: Unexpected format - {type(point)}")

if __name__ == "__main__":
    asyncio.run(check_qdrant_content())
