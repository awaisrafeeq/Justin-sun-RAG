#!/usr/bin/env python
"""Check Record object structure."""

import asyncio
from app.storage.vector_store import VectorStore

async def check_record_structure():
    """Check Record object structure."""
    store = VectorStore()
    await store.ensure_collection()
    
    # Get all points
    result = store.client.scroll(
        collection_name='document_chunks',
        limit=2
    )
    
    if isinstance(result, tuple) and len(result) > 0:
        points = result[0]
        record = points[0]
        print(f"Record type: {type(record)}")
        print(f"Record attributes: {[attr for attr in dir(record) if not attr.startswith('_')]}")
        print(f"Has id: {hasattr(record, 'id')}")
        print(f"Has payload: {hasattr(record, 'payload')}")
        print(f"Has vector: {hasattr(record, 'vector')}")
        
        # Try to access common attributes
        for attr in ['id', 'payload', 'vector', 'score']:
            if hasattr(record, attr):
                try:
                    value = getattr(record, attr)
                    print(f"{attr}: {type(value)} - {str(value)[:100] if value else 'None'}")
                except Exception as e:
                    print(f"{attr}: Error - {e}")

if __name__ == "__main__":
    asyncio.run(check_record_structure())
