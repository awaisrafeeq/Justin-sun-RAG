#!/usr/bin/env python3
"""
Check Qdrant database for stored chunks and embeddings data.
"""

import asyncio
from qdrant_client import QdrantClient
from qdrant_client.http import AsyncApiClient
from qdrant_client.http.models import CollectionsResponse

async def check_qdrant_data():
    """Check what's stored in Qdrant."""
    
    try:
        # Connect to Qdrant
        client = QdrantClient(
            host="localhost",  # Use localhost instead of settings
            port=6333,
            api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.KCUmkp2mfvaAbFclpBIzA9nH3XC48W3TeYw2uFmbX0k",  # Use actual API key
            verify=False  # Disable SSL verification for local dev
        )
        
        print("🔍 Connecting to Qdrant...")
        print(f"Host: localhost")
        print(f"Port: 6333")
        
        # List all collections
        try:
            collections = client.get_collections()
            print(f"\n📁 Collections: {[col.name for col in collections]}")
        except Exception as e:
            print(f"❌ Error getting collections: {e}")
            return
        
        collection_name = "podcast_chunks"
        
        # Check if our collection exists
        try:
            collection_info = client.get_collection(collection_name)
            print(f"\n📊 Collection '{collection_name}' info:")
            print(f"  - Vectors: {collection_info.vectors_count}")
            print(f"  - Status: {collection_info.status}")
            print(f"  - Vector Size: {collection_info.config.params.vectors.size}")
        except Exception as e:
            print(f"❌ Collection '{collection_name}' not found: {e}")
            return
        
        # Get some sample points
        try:
            print(f"\n🔎 Getting sample data from '{collection_name}'...")
            
            # Scroll to get some points
            scroll_result = client.scroll(
                collection_name=collection_name,
                limit=10,
                with_payload=True,
                with_vectors=True
            )
            
            points = scroll_result[0]  # First element contains points
            
            if points:
                print(f"📝 Found {len(points)} sample chunks:")
                for i, point in enumerate(points[:5]):  # Show first 5
                    print(f"\n  Chunk {i+1}:")
                    print(f"    ID: {point.id}")
                    print(f"    Text: {point.payload.get('text', 'No text')[:100]}...")
                    print(f"    Episode ID: {point.payload.get('episode_id')}")
                    print(f"    Chunk Index: {point.payload.get('chunk_index')}")
                    print(f"    Vector dimensions: {len(point.vector) if point.vector else 'No vector'}")
                    
                    # Show some metadata
                    metadata = {k: v for k, v in point.payload.items() 
                              if k not in ['text', 'episode_id', 'chunk_index']}
                    if metadata:
                        print(f"    Metadata: {metadata}")
            else:
                print("❌ No points found in collection")
                
        except Exception as e:
            print(f"❌ Error getting sample data: {e}")
        
        # Get total count
        try:
            count_result = client.count(
                collection_name=collection_name
            )
            print(f"\n📈 Total chunks in database: {count_result.count}")
        except Exception as e:
            print(f"❌ Error getting count: {e}")
            
    except Exception as e:
        print(f"❌ Error connecting to Qdrant: {e}")

if __name__ == "__main__":
    asyncio.run(check_qdrant_data())
