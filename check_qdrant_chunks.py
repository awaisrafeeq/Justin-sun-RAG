#!/usr/bin/env python3
"""
Check Qdrant stored chunks for episode
"""

import asyncio
from app.storage.vector_store import VectorStore

async def check_qdrant_data():
    vector_store = VectorStore()
    
    # Get chunks for the episode
    chunks = await vector_store.get_chunks_by_episode('f3f26e34-73d2-42b3-8a16-623c5346eb1a')
    
    print(f'📊 Total chunks stored: {len(chunks)}')
    print()
    
    for i, chunk in enumerate(chunks):
        print(f'🧩 Chunk {i+1}:')
        print(f'  ID: {chunk["chunk_id"]}')
        print(f'  Index: {chunk["chunk_index"]}')
        print(f'  Text: {chunk["text"]}')
        print(f'  Episode: {chunk["metadata"]["episode_title"]}')
        print()

if __name__ == "__main__":
    asyncio.run(check_qdrant_data())
