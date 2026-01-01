#!/usr/bin/env python
"""Test OpenAI connectivity."""

import asyncio
import os
from app.services.query_embedding import QueryEmbeddingService

async def test_openai_connection():
    """Test OpenAI API connection."""
    try:
        embedding_service = QueryEmbeddingService()
        
        # Test basic embedding
        print("Testing OpenAI connection...")
        result = await embedding_service.embed_query("test")
        
        print(f"✅ Embedding successful!")
        print(f"Embedding length: {len(result)}")
        print(f"First 5 values: {result[:5]}")
        
    except Exception as e:
        print(f"❌ Embedding failed: {e}")
        
        # Check API key
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            print(f"✅ API key found: {api_key[:10]}...")
        else:
            print("❌ No OPENAI_API_KEY found in environment")

if __name__ == "__main__":
    asyncio.run(test_openai_connection())
