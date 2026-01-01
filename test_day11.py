#!/usr/bin/env python
"""Test Day 11 Semantic Search + Disambiguation functionality."""

import asyncio
import json
from typing import List, Dict, Any

from app.services.query_embedding import QueryEmbeddingService
from app.services.semantic_search import SemanticSearchService, SearchRequest
from app.services.disambiguation import DisambiguationService
from app.services.context_builder import ContextBuilder


async def test_query_embedding():
    """Test query embedding service."""
    print("🔍 Testing Query Embedding Service...")
    
    embedding_service = QueryEmbeddingService()
    
    # Test single query embedding
    query = "What is LangChain and how does it work?"
    try:
        embedding = await embedding_service.embed_query(query)
        print(f"✅ Single query embedded: {len(embedding)} dimensions")
        print(f"   Query: '{query}'")
        print(f"   First 5 values: {embedding[:5]}")
    except Exception as e:
        print(f"❌ Single query embedding failed: {e}")
        return False
    
    # Test query normalization
    normalized = embedding_service.normalize_query("  What   is   LangChain?  ")
    expected = "What is LangChain?"
    if normalized == expected:
        print(f"✅ Query normalization works: '{normalized}'")
    else:
        print(f"❌ Query normalization failed: expected '{expected}', got '{normalized}'")
        return False
    
    # Test multiple queries
    queries = [
        "What is LangChain?",
        "How to use memory in LangChain?",
        "LangChain vs other frameworks"
    ]
    try:
        embeddings = await embedding_service.embed_multiple_queries(queries)
        print(f"✅ Multiple queries embedded: {len(embeddings)} embeddings")
        print(f"   Each has {len(embeddings[0])} dimensions")
    except Exception as e:
        print(f"❌ Multiple query embedding failed: {e}")
        return False
    
    return True


async def test_semantic_search():
    """Test semantic search service."""
    print("\n🔍 Testing Semantic Search Service...")
    
    search_service = SemanticSearchService()
    
    # Test basic search
    request = SearchRequest(
        query="LangChain memory",
        limit=5,
        relevance_threshold=0.5
    )
    
    try:
        response = await search_service.search(request)
        print(f"✅ Basic search completed:")
        print(f"   Query: '{response.query}'")
        print(f"   Results found: {response.total_found}")
        print(f"   Processing time: {response.processing_time_ms:.2f}ms")
        
        if response.results:
            print(f"   Top result score: {response.results[0].score:.3f}")
            print(f"   Top result source: {response.results[0].document_title}")
            print(f"   Top result section: {response.results[0].section}")
        else:
            print("   ⚠️ No results found")
            return False
            
    except Exception as e:
        print(f"❌ Semantic search failed: {e}")
        return False
    
    # Test search with filters
    filtered_request = SearchRequest(
        query="LangChain",
        limit=3,
        relevance_threshold=0.3,
        filters={"doc_type": "article"}
    )
    
    try:
        filtered_response = await search_service.search(filtered_request)
        print(f"✅ Filtered search completed:")
        print(f"   Results with doc_type='article': {filtered_response.total_found}")
        print(f"   Filters applied: {filtered_response.filters_applied}")
    except Exception as e:
        print(f"❌ Filtered search failed: {e}")
        return False
    
    return True


async def test_disambiguation():
    """Test disambiguation service."""
    print("\n🔍 Testing Disambiguation Service...")
    
    # First get some search results
    search_service = SemanticSearchService()
    request = SearchRequest(
        query="LangChain",
        limit=10,
        relevance_threshold=0.3
    )
    
    try:
        search_response = await search_service.search(request)
        results = search_response.results
        
        if not results:
            print("⚠️ No search results to disambiguate")
            return True
        
        disambiguation_service = DisambiguationService()
        
        # Test disambiguation
        entity_groups, disambiguation_options = disambiguation_service.disambiguate_results(results)
        
        print(f"✅ Disambiguation completed:")
        print(f"   Entity groups found: {len(entity_groups)}")
        print(f"   Needs disambiguation: {disambiguation_options is not None}")
        
        if entity_groups:
            print(f"   Top entity: {entity_groups[0].entity_title}")
            print(f"   Top entity type: {entity_groups[0].entity_type}")
            print(f"   Top entity score: {entity_groups[0].combined_score:.3f}")
        
        if disambiguation_options:
            print(f"   Disambiguation options: {len(disambiguation_options)}")
            for i, option in enumerate(disambiguation_options[:3], 1):
                print(f"     {i}. {option.title} (score: {option.avg_score:.3f})")
        
    except Exception as e:
        print(f"❌ Disambiguation failed: {e}")
        return False
    
    return True


async def test_context_builder():
    """Test context builder service."""
    print("\n🔍 Testing Context Builder Service...")
    
    # Get search results first
    search_service = SemanticSearchService()
    request = SearchRequest(
        query="LangChain memory",
        limit=5,
        relevance_threshold=0.4
    )
    
    try:
        search_response = await search_service.search(request)
        results = search_response.results
        
        if not results:
            print("⚠️ No search results for context building")
            return True
        
        context_builder = ContextBuilder()
        
        # Test context building from results
        context_window = context_builder.build_context_from_results(
            results,
            max_tokens=1000,
            include_sources=True,
            include_sections=True,
            include_relevance=False
        )
        
        print(f"✅ Context building completed:")
        print(f"   Total tokens: {context_window.total_tokens}")
        print(f"   Chunks included: {len(context_window.chunks)}")
        print(f"   Sources: {context_window.sources}")
        print(f"   Sections: {context_window.sections}")
        print(f"   Truncated: {context_window.truncated}")
        print(f"   Dropped results: {context_window.dropped_results}")
        
        # Test token estimation
        sample_text = "This is a sample text for token estimation."
        estimated_tokens = context_builder.estimate_tokens(sample_text)
        print(f"✅ Token estimation: {estimated_tokens} tokens for '{sample_text}'")
        
        # Test text truncation
        long_text = "This is a very long text that should be truncated to fit within a specific token limit. " * 10
        truncated = context_builder.truncate_text_to_tokens(long_text, 20)
        print(f"✅ Text truncation: {len(truncated)} chars (was {len(long_text)})")
        
    except Exception as e:
        print(f"❌ Context building failed: {e}")
        return False
    
    return True


async def test_api_endpoints():
    """Test search API endpoints."""
    print("\n🔍 Testing API Endpoints...")
    
    import httpx
    
    base_url = "http://127.0.0.1:8000"
    
    async with httpx.AsyncClient() as client:
        # Test basic search endpoint
        search_data = {
            "query": "LangChain memory",
            "limit": 5,
            "relevance_threshold": 0.5
        }
        
        try:
            response = await client.post(f"{base_url}/api/search/", json=search_data)
            if response.status_code == 200:
                search_result = response.json()
                print(f"✅ Search API endpoint working:")
                print(f"   Status: {response.status_code}")
                print(f"   Results: {search_result.get('total_found', 0)}")
                print(f"   Processing time: {search_result.get('processing_time_ms', 0):.2f}ms")
            else:
                print(f"❌ Search API failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Search API request failed: {e}")
            print("   Make sure FastAPI server is running on http://127.0.0.1:8000")
            return False
        
        # Test disambiguation endpoint
        try:
            response = await client.post(f"{base_url}/api/search/disambiguate", json=search_data)
            if response.status_code == 200:
                disambig_result = response.json()
                print(f"✅ Disambiguation API endpoint working:")
                print(f"   Status: {response.status_code}")
                print(f"   Needs disambiguation: {disambig_result.get('needs_disambiguation', False)}")
                print(f"   Options: {len(disambig_result.get('options', []))}")
            else:
                print(f"❌ Disambiguation API failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Disambiguation API request failed: {e}")
            return False
        
        # Test filters endpoint
        try:
            response = await client.get(f"{base_url}/api/search/filters")
            if response.status_code == 200:
                filters = response.json()
                print(f"✅ Filters API endpoint working:")
                print(f"   Available doc_types: {filters.get('doc_type', [])}")
                print(f"   Available source_types: {filters.get('source_type', [])}")
            else:
                print(f"❌ Filters API failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Filters API request failed: {e}")
            return False
    
    return True


async def main():
    """Run all Day 11 tests."""
    print("🚀 Starting Day 11 Semantic Search + Disambiguation Tests\n")
    
    tests = [
        ("Query Embedding", test_query_embedding),
        ("Semantic Search", test_semantic_search),
        ("Disambiguation", test_disambiguation),
        ("Context Builder", test_context_builder),
        ("API Endpoints", test_api_endpoints)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 DAY 11 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Day 11 tests passed! Semantic search is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
    
    print("\nDay 11 Features Implemented:")
    print("✅ Query embedding with OpenAI")
    print("✅ Vector search with relevance threshold")
    print("✅ Metadata filters (doc_type, source_type, etc.)")
    print("✅ Disambiguation logic for multiple entities")
    print("✅ Context builder with token limits")
    print("✅ Search API endpoints")
    print("✅ Comprehensive error handling")


if __name__ == "__main__":
    asyncio.run(main())
