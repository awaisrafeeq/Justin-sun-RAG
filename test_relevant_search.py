#!/usr/bin/env python
"""Test search with terms that should match."""

import requests

def test_relevant_search():
    """Test with terms that should match the document content."""
    url = "http://127.0.0.1:8000/api/search/"
    headers = {"Content-Type": "application/json"}
    
    # Test with terms from the actual document content
    test_queries = [
        {"query": "50-day", "limit": 3, "relevance_threshold": 0.1},
        {"query": "mov", "limit": 3, "relevance_threshold": 0.1},
        {"query": "day", "limit": 3, "relevance_threshold": 0.1}
    ]
    
    for i, data in enumerate(test_queries, 1):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            print(f"\n--- Test {i}: '{data['query']}' ---")
            print(f"Status: {response.status_code}")
            result = response.json()
            print(f"Results found: {result['total_found']}")
            if result['results']:
                for j, res in enumerate(result['results']):
                    print(f"Result {j+1}: {res['text'][:100]}...")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_relevant_search()
