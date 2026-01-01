#!/usr/bin/env python
"""Debug search results."""

import asyncio
from app.services.query_handler import QueryHandlerService, QueryHandlerRequest

async def debug_search():
    """Debug why search returns 0 results."""
    try:
        handler = QueryHandlerService()
        
        # Test with a simple query
        request = QueryHandlerRequest(
            query="LangChain",
            relevance_threshold=0.5
        )
        
        print("Processing query...")
        response = await handler.process_query(request)
        
        print(f"Query: {response.query}")
        print(f"KB Results: {response.kb_results_count}")
        print(f"Context length: {len(response.context)}")
        print(f"Sources: {len(response.sources)}")
        
        if response.metadata:
            print(f"Metadata: {response.metadata}")
        
        if response.search_results:
            print(f"Search results: {len(response.search_results)}")
            for i, result in enumerate(response.search_results[:2]):
                print(f"  Result {i+1}: {result.text[:100]}...")
                print(f"    Score: {result.score}")
        else:
            print("No search results found")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_search())
