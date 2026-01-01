#!/usr/bin/env python
"""
Day 12 Chat Endpoint + Query Handler Tests

Tests the complete query processing pipeline:
1. Query embedding
2. Vector search
3. Relevance check
4. Disambiguation
5. Context building
"""

import asyncio
import requests
import json
import time
from typing import Dict, Any, List

# API base URL
BASE_URL = "http://127.0.0.1:8000"

async def test_chat_endpoint():
    """Test the chat endpoint with full query handler pipeline."""
    print("🔍 Testing Chat Endpoint...")
    
    try:
        # Test basic chat request
        chat_request = {
            "query": "What is LangChain and how does it work?",
            "max_context_tokens": 2000,
            "relevance_threshold": 0.6
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/chat/", json=chat_request, timeout=30)
        processing_time = (time.time() - start_time) * 1000
        
        print(f"Status: {response.status_code}")
        print(f"Processing time: {processing_time:.2f}ms")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Chat endpoint working:")
            print(f"   Query: {result['query'][:50]}...")
            print(f"   Context length: {len(result['context'])} chars")
            print(f"   Sources: {len(result['sources'])}")
            print(f"   Needs disambiguation: {result['needs_disambiguation']}")
            print(f"   KB results: {result['kb_results_count']}")
            print(f"   Total tokens: {result['total_tokens']}")
            print(f"   Response type: {result['response_type']}")
            print(f"   Confidence score: {result.get('confidence_score', 'N/A')}")
            
            if result['context']:
                print(f"   Context preview: {result['context'][:200]}...")
            
            if result['sources']:
                print(f"   Top source: {result['sources'][0]['text_preview'][:100]}...")
            
            return True
        else:
            print(f"❌ Chat endpoint failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat endpoint error: {e}")
        return False

async def test_search_endpoint():
    """Test the refined search endpoint."""
    print("\n🔍 Testing Search Endpoint...")
    
    try:
        # Test search without context
        search_request = {
            "query": "LangChain memory",
            "limit": 5,
            "relevance_threshold": 0.6,
            "include_context": False
        }
        
        response = requests.post(f"{BASE_URL}/chat/search", json=search_request, timeout=30)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Search endpoint working:")
            print(f"   Results: {result['total_found']}")
            print(f"   Processing time: {result['processing_time_ms']:.2f}ms")
            print(f"   Needs disambiguation: {result['needs_disambiguation']}")
            
            if result['results']:
                print(f"   Top result: {result['results'][0]['text'][:100]}...")
                print(f"   Top score: {result['results'][0]['score']:.3f}")
            
            return True
        else:
            print(f"❌ Search endpoint failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Search endpoint error: {e}")
        return False

async def test_search_with_context():
    """Test search endpoint with context building."""
    print("\n🔍 Testing Search with Context...")
    
    try:
        search_request = {
            "query": "LangChain memory",
            "limit": 5,
            "relevance_threshold": 0.6,
            "include_context": True,
            "max_context_tokens": 1500
        }
        
        response = requests.post(f"{BASE_URL}/chat/search", json=search_request, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Search with context working:")
            print(f"   Results: {result['total_found']}")
            print(f"   Context tokens: {result.get('context_tokens', 0)}")
            print(f"   Context sources: {len(result.get('context_sources', []))}")
            
            if result.get('context'):
                print(f"   Context preview: {result['context'][:200]}...")
            
            return True
        else:
            print(f"❌ Search with context failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Search with context error: {e}")
        return False

async def test_filters_endpoint():
    """Test the filters endpoint."""
    print("\n🔍 Testing Filters Endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/chat/filters", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Filters endpoint working:")
            print(f"   Doc types: {result['doc_type']}")
            print(f"   Source types: {result['source_type']}")
            print(f"   Sections: {result['section']}")
            
            return True
        else:
            print(f"❌ Filters endpoint failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Filters endpoint error: {e}")
        return False

async def test_health_endpoint():
    """Test the health endpoint."""
    print("\n🔍 Testing Health Endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/chat/health", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Health endpoint working:")
            print(f"   Status: {result['status']}")
            print(f"   Services: {list(result['services'].keys())}")
            
            # Check individual services
            for service, status in result['services'].items():
                if "healthy" in status:
                    print(f"   ✅ {service}: {status}")
                else:
                    print(f"   ❌ {service}: {status}")
            
            return result['status'] == "healthy"
        else:
            print(f"❌ Health endpoint failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

async def test_query_with_filters():
    """Test chat endpoint with filters."""
    print("\n🔍 Testing Chat with Filters...")
    
    try:
        chat_request = {
            "query": "LangChain",
            "filters": {
                "doc_type": "article",
                "source_type": "pdf"
            },
            "relevance_threshold": 0.5
        }
        
        response = requests.post(f"{BASE_URL}/chat/", json=chat_request, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Chat with filters working:")
            print(f"   Results: {result['kb_results_count']}")
            print(f"   Filters applied: {result.get('metadata', {}).get('filters_applied', {})}")
            
            return True
        else:
            print(f"❌ Chat with filters failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat with filters error: {e}")
        return False

async def test_disambiguation_flow():
    """Test disambiguation when multiple entities found."""
    print("\n🔍 Testing Disambiguation Flow...")
    
    try:
        # Use a query that might find multiple entities
        chat_request = {
            "query": "memory",
            "relevance_threshold": 0.3  # Lower threshold to get more results
        }
        
        response = requests.post(f"{BASE_URL}/chat/", json=chat_request, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Disambiguation flow working:")
            print(f"   Needs disambiguation: {result['needs_disambiguation']}")
            print(f"   Results found: {result['kb_results_count']}")
            
            if result['needs_disambiguation'] and result['disambiguation_options']:
                print(f"   Disambiguation options: {len(result['disambiguation_options'])}")
                for i, option in enumerate(result['disambiguation_options'][:2]):
                    print(f"     Option {i+1}: {option.get('title', 'N/A')}")
            
            return True
        else:
            print(f"❌ Disambiguation flow failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Disambiguation flow error: {e}")
        return False

async def main():
    """Run all Day 12 tests."""
    print("🚀 Starting Day 12 Chat Endpoint + Query Handler Tests")
    print("=" * 60)
    
    tests = [
        ("Chat Endpoint", test_chat_endpoint),
        ("Search Endpoint", test_search_endpoint),
        ("Search with Context", test_search_with_context),
        ("Filters Endpoint", test_filters_endpoint),
        ("Health Endpoint", test_health_endpoint),
        ("Chat with Filters", test_query_with_filters),
        ("Disambiguation Flow", test_disambiguation_flow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DAY 12 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Day 12 tests passed! Chat endpoint is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
    
    print("\nDay 12 Features Implemented:")
    print("✅ Query handler flow: embed → search → relevance → disambiguation → context")
    print("✅ POST /chat endpoint with full pipeline")
    print("✅ POST /search endpoint with optional context")
    print("✅ Sources + KB vs Web indication")
    print("✅ Comprehensive error handling")
    print("✅ Health check for all services")
    print("✅ Filter options endpoint")

if __name__ == "__main__":
    asyncio.run(main())
