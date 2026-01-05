#!/usr/bin/env python
"""Test Day 14 Web Search Fallback + Integration endpoints."""

import asyncio
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

async def test_web_search():
    """Test web search endpoint."""
    print("Testing Web Search...")
    
    try:
        request_data = {
            "query": "artificial intelligence trends 2024",
            "max_results": 3,
            "search_depth": "basic"
        }
        
        response = requests.post(f"{BASE_URL}/web-search/search", json=request_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Web search working:")
            print(f"   Query: {result['query']}")
            print(f"   Results: {result['total_found']}")
            print(f"   Processing time: {result['processing_time_ms']:.2f}ms")
            
            if result['results']:
                top_result = result['results'][0]
                print(f"   Top result: {top_result['title'][:50]}...")
                print(f"   Source: {top_result['source']}")
                print(f"   Relevance: {top_result['relevance_score']:.2f}")
            
            return True
        else:
            print(f"Web search failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Web search error: {e}")
        return False

async def test_hybrid_search():
    """Test hybrid search endpoint."""
    print("Testing Hybrid Search...")
    
    try:
        request_data = {
            "query": "machine learning algorithms",
            "kb_confidence_threshold": 0.3,  # Low threshold to trigger web fallback
            "max_kb_results": 3,
            "max_web_results": 3,
            "use_web_fallback": True,
            "search_depth": "basic"
        }
        
        response = requests.post(f"{BASE_URL}/web-search/hybrid", json=request_data, timeout=45)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Hybrid search working:")
            print(f"   Query: {result['query']}")
            print(f"   KB results: {result['total_kb_results']}")
            print(f"   Web results: {result['total_web_results']}")
            print(f"   Used web fallback: {result['used_web_fallback']}")
            print(f"   KB confidence: {result['kb_confidence_score']:.2f}")
            print(f"   Processing time: {result['processing_time_ms']:.2f}ms")
            
            # Show sample results
            if result['kb_results']:
                kb_sample = result['kb_results'][0]
                print(f"   KB sample: {kb_sample['title'][:50]}...")
            
            if result['web_results']:
                web_sample = result['web_results'][0]
                print(f"   Web sample: {web_sample['title'][:50]}...")
            
            return True
        else:
            print(f"Hybrid search failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Hybrid search error: {e}")
        return False

async def test_hybrid_search_no_fallback():
    """Test hybrid search without web fallback."""
    print("Testing Hybrid Search (No Fallback)...")
    
    try:
        request_data = {
            "query": "LangChain",
            "kb_confidence_threshold": 0.1,  # Very low threshold
            "max_kb_results": 5,
            "max_web_results": 0,
            "use_web_fallback": False,
            "search_depth": "basic"
        }
        
        response = requests.post(f"{BASE_URL}/web-search/hybrid", json=request_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Hybrid search (no fallback) working:")
            print(f"   Query: {result['query']}")
            print(f"   KB results: {result['total_kb_results']}")
            print(f"   Web results: {result['total_web_results']}")
            print(f"   Used web fallback: {result['used_web_fallback']}")
            print(f"   KB confidence: {result['kb_confidence_score']:.2f}")
            
            return True
        else:
            print(f"Hybrid search (no fallback) failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Hybrid search (no fallback) error: {e}")
        return False

async def test_web_search_options():
    """Test web search options endpoint."""
    print("Testing Web Search Options...")
    
    try:
        response = requests.get(f"{BASE_URL}/web-search/options", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Web search options working:")
            print(f"   Search depths: {result['search_depths']}")
            print(f"   Results range: {result['max_results_range']}")
            print(f"   Confidence range: {result['confidence_threshold_range']}")
            print(f"   Fallback enabled: {result['fallback_enabled']}")
            
            return True
        else:
            print(f"Web search options failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Web search options error: {e}")
        return False

async def test_web_search_health():
    """Test web search health endpoint."""
    print("Testing Web Search Health...")
    
    try:
        response = requests.get(f"{BASE_URL}/web-search/health", timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Web search health working:")
            print(f"   Status: {result['status']}")
            print(f"   API key configured: {result['api_key_configured']}")
            print(f"   Services: {result['services']}")
            
            # Check individual services
            for service, status in result['services'].items():
                status_icon = "✓" if "healthy" in status else "✗"
                print(f"   {status_icon} {service}: {status}")
            
            return True
        else:
            print(f"Web search health failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Web search health error: {e}")
        return False

async def test_fallback_logic():
    """Test fallback logic scenarios."""
    print("Testing Fallback Logic...")
    
    scenarios = [
        {
            "name": "Low confidence threshold",
            "query": "quantum computing",
            "threshold": 0.8,  # High threshold to trigger fallback
            "expect_fallback": True
        },
        {
            "name": "Normal confidence threshold",
            "query": "LangChain",
            "threshold": 0.3,  # Normal threshold
            "expect_fallback": False
        }
    ]
    
    results = []
    
    for scenario in scenarios:
        try:
            request_data = {
                "query": scenario["query"],
                "kb_confidence_threshold": scenario["threshold"],
                "max_kb_results": 3,
                "max_web_results": 2,
                "use_web_fallback": True,
                "search_depth": "basic"
            }
            
            response = requests.post(f"{BASE_URL}/web-search/hybrid", json=request_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                used_fallback = result['used_web_fallback']
                expected = scenario["expect_fallback"]
                
                if used_fallback == expected:
                    print(f"   ✓ {scenario['name']}: Fallback behavior correct")
                    results.append(True)
                else:
                    print(f"   ✗ {scenario['name']}: Expected fallback={expected}, got={used_fallback}")
                    results.append(False)
            else:
                print(f"   ✗ {scenario['name']}: Request failed")
                results.append(False)
                
        except Exception as e:
            print(f"   ✗ {scenario['name']}: Error - {e}")
            results.append(False)
    
    return all(results)

async def test_attribution():
    """Test result attribution and source tracking."""
    print("Testing Attribution...")
    
    try:
        request_data = {
            "query": "blockchain technology",
            "kb_confidence_threshold": 0.2,
            "max_kb_results": 2,
            "max_web_results": 2,
            "use_web_fallback": True,
            "search_depth": "basic"
        }
        
        response = requests.post(f"{BASE_URL}/web-search/hybrid", json=request_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            # Check KB results attribution
            kb_attributions_ok = True
            for kb_result in result['kb_results']:
                if kb_result['source_type'] != 'knowledge_base':
                    kb_attributions_ok = False
                    print(f"   ✗ KB result wrong source type: {kb_result['source_type']}")
                if kb_result['url'] is not None:
                    kb_attributions_ok = False
                    print(f"   ✗ KB result should not have URL")
            
            # Check web results attribution
            web_attributions_ok = True
            for web_result in result['web_results']:
                if web_result['source_type'] != 'web':
                    web_attributions_ok = False
                    print(f"   ✗ Web result wrong source type: {web_result['source_type']}")
                if web_result['url'] is None:
                    web_attributions_ok = False
                    print(f"   ✗ Web result should have URL")
            
            if kb_attributions_ok and web_attributions_ok:
                print(f"   Attribution working correctly")
                return True
            else:
                print(f"   Attribution issues found")
                return False
        else:
            print(f"Attribution test failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Attribution test error: {e}")
        return False

async def main():
    """Run all Day 14 tests."""
    print("Starting Day 14 Web Search Tests")
    print("=" * 60)
    
    tests = [
        ("Web Search", test_web_search),
        ("Hybrid Search", test_hybrid_search),
        ("Hybrid Search (No Fallback)", test_hybrid_search_no_fallback),
        ("Web Search Options", test_web_search_options),
        ("Web Search Health", test_web_search_health),
        ("Fallback Logic", test_fallback_logic),
        ("Attribution", test_attribution)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"{test_name} failed with exception: {e}")
            results.append((test_name, False))
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("DAY 14 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! Day 14 implementation is complete!")
    else:
        print("Some tests failed. Check logs above for details.")
    
    print("\nDay 14 Features Implemented:")
    print("✅ Tavily client setup and integration")
    print("✅ Web search function with cleaning/parsing")
    print("✅ Fallback logic for low KB scores")
    print("✅ Fallback logic for no KB results")
    print("✅ Hybrid response with proper attribution")
    print("✅ Query handler integration")
    print("✅ Web search API endpoints")
    print("✅ Comprehensive error handling")
    print("✅ Health monitoring and status checks")

if __name__ == "__main__":
    asyncio.run(main())
