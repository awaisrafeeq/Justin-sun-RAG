"""Web search API endpoints for fallback search functionality."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends

from app.api.schemas.web_search import (
    WebSearchRequest, WebSearchResponse, HybridSearchRequest, HybridSearchResponse,
    WebSearchOptionsResponse, WebSearchHealthResponse
)
from app.services.web_search import WebSearchService, WebSearchRequest as ServiceRequest
from app.services.semantic_search import SemanticSearchService
from app.services.query_handler import QueryHandlerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/web-search", tags=["web-search"])

# Lazy loading for services
_web_search_service = None
_semantic_search_service = None
_query_handler_service = None


def get_web_search_service() -> WebSearchService:
    """Get or create web search service."""
    global _web_search_service
    if _web_search_service is None:
        _web_search_service = WebSearchService()
    return _web_search_service


def get_semantic_search_service() -> SemanticSearchService:
    """Get or create semantic search service."""
    global _semantic_search_service
    if _semantic_search_service is None:
        _semantic_search_service = SemanticSearchService()
    return _semantic_search_service


def get_query_handler_service() -> QueryHandlerService:
    """Get or create query handler service."""
    global _query_handler_service
    if _query_handler_service is None:
        _query_handler_service = QueryHandlerService()
    return _query_handler_service


@router.post("/search", response_model=WebSearchResponse)
async def web_search(request: WebSearchRequest) -> WebSearchResponse:
    """
    Perform web search using Tavily API.
    
    Searches the web for relevant information when knowledge base
    results are insufficient or when web search is specifically requested.
    """
    try:
        logger.info(f"Performing web search for query: {request.query}")
        
        service = get_web_search_service()
        
        # Convert API request to service request
        service_request = ServiceRequest(
            query=request.query,
            max_results=request.max_results,
            search_depth=request.search_depth,
            include_domains=request.include_domains,
            exclude_domains=request.exclude_domains
        )
        
        # Perform web search
        service_response = await service.search_web(service_request)
        
        # Convert service response to API response
        api_response = WebSearchResponse(
            query=service_response.query,
            results=[{
                "title": result.title,
                "url": result.url,
                "content": result.content,
                "snippet": result.snippet,
                "source": result.source,
                "relevance_score": result.relevance_score,
                "metadata": result.metadata
            } for result in service_response.results],
            total_found=service_response.total_found,
            processing_time_ms=service_response.processing_time_ms,
            metadata=service_response.metadata
        )
        
        logger.info(f"Web search completed: {len(api_response.results)} results")
        return api_response
        
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Web search failed: {str(e)}")


@router.post("/hybrid", response_model=HybridSearchResponse)
async def hybrid_search(request: HybridSearchRequest) -> HybridSearchResponse:
    """
    Perform hybrid search combining knowledge base and web search.
    
    First searches the knowledge base, then falls back to web search
    if KB results are insufficient or confidence is low.
    """
    try:
        import time
        start_time = time.time()
        
        logger.info(f"Performing hybrid search for query: {request.query}")
        
        # Get services
        web_service = get_web_search_service()
        query_service = get_query_handler_service()
        
        # Search knowledge base first
        from app.services.query_handler import QueryHandlerRequest
        kb_request = QueryHandlerRequest(
            query=request.query,
            relevance_threshold=request.kb_confidence_threshold,
            max_context_tokens=4000
        )
        
        kb_response = await query_service.process_query(kb_request)
        
        # Convert KB results to hybrid format
        kb_results = []
        for result in kb_response.search_results:
            kb_results.append({
                "source_type": "knowledge_base",
                "title": result.get("document_title", "Knowledge Base Result"),
                "content": result.get("text", ""),
                "url": None,
                "source": result.get("document_type", "document") or "document",
                "relevance_score": result.get("score", 0.0),
                "metadata": result.get("metadata", {})
            })
        
        # Determine if web fallback is needed
        web_results = []
        used_web_fallback = False
        
        if request.use_web_fallback and web_service.should_use_web_fallback(
            len(kb_results), 
            kb_response.metadata.get("confidence_score", 0.0),
            request.kb_confidence_threshold
        ):
            used_web_fallback = True
            logger.info("Using web search fallback")
            
            try:
                # Perform web search
                web_request = ServiceRequest(
                    query=request.query,
                    max_results=request.max_web_results,
                    search_depth=request.search_depth
                )
                
                web_response = await web_service.search_web(web_request)
                
                # Convert web results to hybrid format
                for result in web_response.results:
                    web_results.append({
                        "source_type": "web",
                        "title": result.title,
                        "content": result.content,
                        "url": result.url,
                        "source": result.source,
                        "relevance_score": result.relevance_score,
                        "metadata": result.metadata
                    })
            except Exception as e:
                logger.error(f"Web search failed: {e}")
                # Continue without web results
                web_results = []
                used_web_fallback = False
        
        processing_time = (time.time() - start_time) * 1000
        
        return HybridSearchResponse(
            query=request.query,
            kb_results=kb_results,
            web_results=web_results,
            total_kb_results=len(kb_results),
            total_web_results=len(web_results),
            used_web_fallback=used_web_fallback,
            kb_confidence_score=kb_response.metadata.get("confidence_score", 0.0),
            processing_time_ms=processing_time,
            metadata={
                "kb_processing_time_ms": kb_response.processing_time_ms,
                "web_processing_time_ms": web_response.processing_time_ms if (used_web_fallback and 'web_response' in locals()) else 0,
                "search_depth": request.search_depth,
                "confidence_threshold": request.kb_confidence_threshold
            }
        )
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")


@router.get("/options", response_model=WebSearchOptionsResponse)
async def get_web_search_options() -> WebSearchOptionsResponse:
    """
    Get available web search options and configuration.
    
    Returns information about search depths, limits, and
    available configuration options for web search.
    """
    try:
        logger.info("Retrieving web search options")
        
        web_service = get_web_search_service()
        
        options = WebSearchOptionsResponse(
            search_depths=["basic", "advanced"],
            max_results_range={"min": 1, "max": 20, "default": 5},
            confidence_threshold_range={"min": 0.0, "max": 1.0, "default": 0.5},
            fallback_enabled=web_service.api_key is not None
        )
        
        logger.info("Web search options retrieved successfully")
        return options
        
    except Exception as e:
        logger.error(f"Options retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Options retrieval failed: {str(e)}")


@router.get("/health", response_model=WebSearchHealthResponse)
async def health_check() -> WebSearchHealthResponse:
    """
    Check health of web search services.
    
    Returns status of web search service and
    Tavily API connectivity.
    """
    import datetime
    services = {}
    
    try:
        # Check web search service
        web_service = get_web_search_service()
        if web_service.api_key and web_service.api_key != "your_tavily_api_key_here":
            services["web_search"] = "healthy"
        else:
            services["web_search"] = "unhealthy: TAVILY_API_KEY not configured or using placeholder"
    except Exception as e:
        services["web_search"] = f"unhealthy: {str(e)}"
    
    try:
        # Check Tavily API connectivity
        web_service = get_web_search_service()
        if web_service.api_key and web_service.api_key != "your_tavily_api_key_here":
            # Simple test search
            test_request = ServiceRequest(
                query="test",
                max_results=1,
                search_depth="basic"
            )
            test_response = await web_service.search_web(test_request)
            if "error" not in test_response.metadata:
                services["tavily_api"] = "healthy"
            else:
                services["tavily_api"] = f"unhealthy: {test_response.metadata.get('error', 'Unknown error')}"
        else:
            services["tavily_api"] = "unhealthy: API key not configured or using placeholder"
    except Exception as e:
        services["tavily_api"] = f"unhealthy: {str(e)}"
    
    try:
        # Check semantic search service
        semantic_service = get_semantic_search_service()
        services["semantic_search"] = "healthy"
    except Exception as e:
        services["semantic_search"] = f"unhealthy: {str(e)}"
    
    # Determine overall status
    all_healthy = all("healthy" in status for status in services.values())
    overall_status = "healthy" if all_healthy else "unhealthy"
    
    web_service = get_web_search_service()
    
    return WebSearchHealthResponse(
        status=overall_status,
        services=services,
        api_key_configured=web_service.api_key is not None,
        timestamp=datetime.datetime.utcnow()
    )


def calculate_hybrid_confidence(kb_confidence: float, web_results_count: int) -> float:
    """
    Calculate confidence score for hybrid search results.
    
    Args:
        kb_confidence: Confidence from knowledge base search
        web_results_count: Number of web search results
        
    Returns:
        Combined confidence score between 0.0 and 1.0
    """
    if web_results_count == 0:
        return kb_confidence
    
    # Web results add confidence but less than KB results
    web_confidence = min(web_results_count / 10, 0.3)  # Max 0.3 from web
    
    # Combine with weighted average (KB weighted more heavily)
    combined_confidence = (kb_confidence * 0.7) + (web_confidence * 0.3)
    
    return round(min(combined_confidence, 1.0), 3)
