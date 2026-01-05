"""Web search service for fallback when knowledge base results are insufficient."""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class WebSearchResult:
    """Result from web search."""
    title: str
    url: str
    content: str
    snippet: str
    source: str
    relevance_score: float
    metadata: Dict[str, Any]


@dataclass
class WebSearchRequest:
    """Request for web search."""
    query: str
    max_results: int = 5
    search_depth: str = "basic"  # "basic" or "advanced"
    include_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None


@dataclass
class WebSearchResponse:
    """Response from web search."""
    query: str
    results: List[WebSearchResult]
    total_found: int
    processing_time_ms: float
    metadata: Dict[str, Any]


class WebSearchService:
    """
    Service for web search using Tavily API.
    
    Provides fallback search when knowledge base results are insufficient
    or when no relevant results are found in the knowledge base.
    """
    
    def __init__(self):
        self.api_key = settings.tavily_api_key
        self.base_url = "https://api.tavily.com/search"
        
        if not self.api_key:
            logger.warning("TAVILY_API_KEY not set. Web search fallback will be disabled.")
        else:
            logger.info("Tavily client initialized with API key")
    
    async def search_web(self, request: WebSearchRequest) -> WebSearchResponse:
        """
        Perform web search using Tavily API.
        
        Args:
            request: Web search request with query and parameters
            
        Returns:
            Web search response with results and metadata
        """
        import time
        start_time = time.time()
        
        try:
            if not self.api_key:
                return WebSearchResponse(
                    query=request.query,
                    results=[],
                    total_found=0,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    metadata={"error": "TAVILY_API_KEY not configured"}
                )
            
            # Prepare Tavily API request
            tavily_request = {
                "api_key": self.api_key,
                "query": request.query,
                "search_depth": request.search_depth,
                "include_answer": True,
                "include_raw_content": False,
                "max_results": request.max_results,
            }
            
            # Add domain filters if specified
            if request.include_domains:
                tavily_request["include_domains"] = request.include_domains
            
            if request.exclude_domains:
                tavily_request["exclude_domains"] = request.exclude_domains
            
            # Make API request
            response = requests.post(
                self.base_url,
                json=tavily_request,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Tavily API error: {response.status_code} - {response.text}")
                return WebSearchResponse(
                    query=request.query,
                    results=[],
                    total_found=0,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    metadata={"error": f"Tavily API error: {response.status_code}"}
                )
            
            # Parse response
            data = response.json()
            results = self._process_tavily_results(data.get("results", []))
            
            return WebSearchResponse(
                query=request.query,
                results=results,
                total_found=len(results),
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={
                    "api_response_time": data.get("response_time", 0),
                    "answer": data.get("answer", ""),
                    "search_depth": request.search_depth
                }
            )
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return WebSearchResponse(
                query=request.query,
                results=[],
                total_found=0,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)}
            )
    
    def _process_tavily_results(self, tavily_results: List[Dict]) -> List[WebSearchResult]:
        """
        Process Tavily API results into WebSearchResult objects.
        
        Args:
            tavily_results: Raw results from Tavily API
            
        Returns:
            Processed WebSearchResult objects
        """
        processed_results = []
        
        for i, result in enumerate(tavily_results):
            try:
                # Extract and clean content
                content = self._clean_text(result.get("content", ""))
                snippet = self._clean_text(result.get("snippet", ""))
                
                # Calculate relevance score (simple heuristic)
                relevance_score = self._calculate_relevance_score(
                    result.get("title", ""),
                    content,
                    snippet
                )
                
                # Extract source domain
                source = self._extract_domain(result.get("url", ""))
                
                web_result = WebSearchResult(
                    title=self._clean_text(result.get("title", "")),
                    url=result.get("url", ""),
                    content=content,
                    snippet=snippet,
                    source=source,
                    relevance_score=relevance_score,
                    metadata={
                        "position": i + 1,
                        "published_date": result.get("published_date"),
                        "score": result.get("score", 0.0)
                    }
                )
                
                processed_results.append(web_result)
                
            except Exception as e:
                logger.warning(f"Failed to process web result {i}: {e}")
                continue
        
        return processed_results
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/]', '', text)
        
        # Trim whitespace
        text = text.strip()
        
        return text
    
    def _calculate_relevance_score(self, title: str, content: str, snippet: str) -> float:
        """
        Calculate relevance score for a web search result.
        
        Args:
            title: Result title
            content: Result content
            snippet: Result snippet
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        score = 0.0
        
        # Title relevance (most important)
        if title:
            title_length = len(title.split())
            score += min(title_length / 10, 0.4)  # Max 0.4 from title
        
        # Content relevance
        if content:
            content_length = len(content.split())
            score += min(content_length / 100, 0.4)  # Max 0.4 from content
        
        # Snippet relevance
        if snippet:
            snippet_length = len(snippet.split())
            score += min(snippet_length / 20, 0.2)  # Max 0.2 from snippet
        
        return min(score, 1.0)
    
    def _extract_domain(self, url: str) -> str:
        """
        Extract domain name from URL.
        
        Args:
            url: Full URL
            
        Returns:
            Domain name
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return "unknown"
    
    def should_use_web_fallback(self, kb_results_count: int, kb_confidence_score: float, 
                               confidence_threshold: float = 0.5) -> bool:
        """
        Determine if web search fallback should be used.
        
        Args:
            kb_results_count: Number of knowledge base results
            kb_confidence_score: Confidence score from KB search
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            True if web fallback should be used
        """
        # Use web fallback if no KB results
        if kb_results_count == 0:
            return True
        
        # Use web fallback if KB confidence is below threshold
        if kb_confidence_score < confidence_threshold:
            return True
        
        return False
    
    async def get_fallback_results(self, query: str, kb_results_count: int, 
                                 kb_confidence_score: float) -> Optional[WebSearchResponse]:
        """
        Get web search results as fallback.
        
        Args:
            query: Search query
            kb_results_count: Number of KB results
            kb_confidence_score: Confidence score from KB
            
        Returns:
            Web search response or None if fallback not needed
        """
        if not self.should_use_web_fallback(kb_results_count, kb_confidence_score):
            return None
        
        logger.info(f"Using web search fallback for query: {query}")
        
        request = WebSearchRequest(
            query=query,
            max_results=5,
            search_depth="basic"
        )
        
        return await self.search_web(request)
