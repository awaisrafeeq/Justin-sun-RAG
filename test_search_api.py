#!/usr/bin/env python
"""Simple test for search API."""

import requests
import json

def test_search_api():
    """Test the search API endpoint."""
    url = "http://127.0.0.1:8000/api/search/"
    headers = {"Content-Type": "application/json"}
    
    # Test with different queries
    test_queries = [
        {"query": "LangChain", "limit": 3, "relevance_threshold": 0.3},
        {"query": "memory", "limit": 3, "relevance_threshold": 0.3},
        {"query": "document", "limit": 3, "relevance_threshold": 0.3},
        {"query": "chunk", "limit": 3, "relevance_threshold": 0.1}
    ]
    
    for i, data in enumerate(test_queries, 1):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            print(f"\n--- Test {i}: '{data['query']}' ---")
            print(f"Status: {response.status_code}")
            result = response.json()
            print(f"Results found: {result['total_found']}")
            if result['results']:
                print(f"Top result: {result['results'][0]['text'][:100]}...")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_search_api()
