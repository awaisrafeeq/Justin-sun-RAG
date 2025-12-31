#!/usr/bin/env python
"""Test Day 10 features"""
import asyncio
from app.storage.vector_store import VectorStore

async def test_day10():
    vs = VectorStore()
    chunks = await vs.get_chunks_by_document('4f8ab15c-d01f-4deb-a477-8280ebf57665')
    print(f'Found {len(chunks)} chunks in Qdrant')
    
    if chunks:
        meta = chunks[0].get('metadata', {})
        print(f'Chunk 0 metadata keys: {list(meta.keys())}')
        print(f'Doc type: {meta.get("doc_type")}')
        print(f'Section: {meta.get("section")}')
        print(f'Source type: {meta.get("source_type")}')
        print(f'Chunk type: {meta.get("chunk_type")}')
        
        # Check a few more chunks
        if len(chunks) > 1:
            meta1 = chunks[1].get('metadata', {})
            print(f'Chunk 1 section: {meta1.get("section")}')
        
        print('\n✅ Day 10 Test Results:')
        print(f'  - Chunks stored: {len(chunks)}')
        print(f'  - Rich metadata: {"✅" if meta.get("doc_type") else "❌"}')
        print(f'  - Section detection: {"✅" if meta.get("section") else "❌"}')
    else:
        print('❌ No chunks found in Qdrant')

if __name__ == "__main__":
    asyncio.run(test_day10())
