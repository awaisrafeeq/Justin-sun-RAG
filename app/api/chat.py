"""
Chat and Search API endpoints for Day 12.

Implements:
- POST /chat - Full query handler pipeline
- POST /search - Refined search endpoint
- GET /filters - Available filter options
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.api.schemas.chat import (
    ChatRequest, ChatResponse, SearchRequest, SearchResponse, 
    FilterOptionsResponse, HealthResponse
)
from app.services.query_handler import QueryHandlerService, QueryHandlerRequest, QueryHandlerResponse
from app.services.semantic_search import SemanticSearchService, SearchRequest as SemanticSearchRequest
from app.services.disambiguation import DisambiguationService
from app.services.context_builder import ContextBuilder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Lazy loading for services
_query_handler_service = None
_semantic_search_service = None
_disambiguation_service = None
_context_builder_service = None

def get_query_handler_service() -> QueryHandlerService:
    """Get or create query handler service."""
    global _query_handler_service
    if _query_handler_service is None:
        _query_handler_service = QueryHandlerService()
    return _query_handler_service

def get_semantic_search_service() -> SemanticSearchService:
    """Get or create semantic search service."""
    global _semantic_search_service
    if _semantic_search_service is None:
        _semantic_search_service = SemanticSearchService()
    return _semantic_search_service

def get_disambiguation_service() -> DisambiguationService:
    """Get or create disambiguation service."""
    global _disambiguation_service
    if _disambiguation_service is None:
        _disambiguation_service = DisambiguationService()
    return _disambiguation_service

def get_context_builder_service() -> ContextBuilder:
    """Get or create context builder service."""
    global _context_builder_service
    if _context_builder_service is None:
        _context_builder_service = ContextBuilder()
    return _context_builder_service


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Chat endpoint with full query handler pipeline.
    
    Processes user query through:
    1. Query embedding
    2. Vector search
    3. Relevance check
    4. Disambiguation
    5. Context building
    
    Returns context, sources, and metadata for response generation.
    """
    try:
        logger.info(f"Chat request received: {request.query[:100]}...")
        
        # Get services
        query_handler = get_query_handler_service()
        
        # Build query handler request
        handler_request = QueryHandlerRequest(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            filters=request.filters,
            max_context_tokens=request.max_context_tokens,
            relevance_threshold=request.relevance_threshold
        )
        
        # Process query
        handler_response = await query_handler.process_query(handler_request)
        
        # Build chat response
        chat_response = ChatResponse(
            query=handler_response.query,
            context=handler_response.context,
            sources=handler_response.sources,
            needs_disambiguation=handler_response.needs_disambiguation,
            disambiguation_options=handler_response.disambiguation_options,
            search_results=handler_response.search_results,
            processing_time_ms=handler_response.processing_time_ms,
            total_tokens=handler_response.total_tokens,
            context_sources_count=handler_response.context_sources_count,
            kb_results_count=handler_response.kb_results_count,
            web_results_count=handler_response.web_results_count,
            response_type="knowledge_base",
            confidence_score=calculate_confidence_score(handler_response)
        )
        
        logger.info(f"Chat response sent: {len(chat_response.context)} chars, {len(chat_response.sources)} sources")
        return chat_response
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@router.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest) -> SearchResponse:
    """
    Refined search endpoint with optional context building.
    
    Performs semantic search and optionally builds context from results.
    """
    try:
        logger.info(f"Search request received: {request.query[:100]}...")
        
        # Get services
        semantic_search = get_semantic_search_service()
        disambiguation = get_disambiguation_service()
        context_builder = get_context_builder_service()
        
        # Perform semantic search
        search_request = SemanticSearchRequest(
            query=request.query,
            limit=request.limit,
            relevance_threshold=request.relevance_threshold,
            filters=request.filters or {}
        )
        
        search_response = await semantic_search.search(search_request)
        
        # Check for disambiguation
        entity_groups, disambiguation_options = disambiguation.disambiguate_results(
            search_response.results,
            max_groups=5,
            min_score_threshold=request.relevance_threshold
        )
        
        needs_disambiguation = disambiguation_options is not None
        
        # Build context if requested
        context = None
        context_sources = None
        context_tokens = None
        
        if request.include_context and search_response.results:
            context_window = context_builder.build_context_from_results(
                search_response.results,
                max_tokens=request.max_context_tokens,
                include_sources=True,
                include_sections=True,
                include_relevance=False
            )
            
            context = _build_context_text(context_window)
            context_sources = [chunk.source for chunk in context_window.chunks]
            context_tokens = context_window.total_tokens
        
        # Build search response
        # Convert SearchResult objects to dictionaries for Pydantic
        results_dict = []
        for result in search_response.results:
            # SearchResult is a dataclass, convert to dict
            results_dict.append({
                "chunk_id": result.chunk_id,
                "document_id": result.document_id,
                "text": result.text,
                "score": result.score,
                "metadata": result.metadata,
                "document_title": result.document_title,
                "document_type": result.document_type,
                "section": result.section
            })
        
        # Convert disambiguation options to dictionaries
        disambiguation_options_dict = None
        if needs_disambiguation and disambiguation_options:
            disambiguation_options_dict = []
            for option in disambiguation_options:
                # DisambiguationOption is a dataclass, convert to dict
                disambiguation_options_dict.append({
                    "group_id": option.group_id,
                    "title": option.title,
                    "description": option.description,
                    "entity_type": option.entity_type,
                    "result_count": option.result_count,
                    "avg_score": option.avg_score,
                    "sample_text": option.sample_text,
                    "metadata": option.metadata
                })
        
        search_response_data = SearchResponse(
            query=request.query,
            results=results_dict,
            total_found=len(search_response.results),
            processing_time_ms=search_response.processing_time_ms,
            context=context,
            context_sources=context_sources,
            context_tokens=context_tokens,
            filters_applied=request.filters,
            relevance_threshold=request.relevance_threshold,
            needs_disambiguation=needs_disambiguation,
            disambiguation_options=disambiguation_options_dict
        )
        
        logger.info(f"Search response sent: {len(search_response_data.results)} results")
        return search_response_data
        
    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Search processing failed: {str(e)}")


@router.get("/filters", response_model=FilterOptionsResponse)
async def get_filters() -> FilterOptionsResponse:
    """
    Get available filter options for search.
    """
    try:
        query_handler = get_query_handler_service()
        filter_options = await query_handler.get_available_filters()
        
        return FilterOptionsResponse(
            doc_type=filter_options.get("doc_type", []),
            source_type=filter_options.get("source_type", []),
            section=filter_options.get("section", [])
        )
        
    except Exception as e:
        logger.error(f"Filters endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get filter options: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check for chat services.
    """
    import datetime
    
    try:
        # Test services
        services = {}
        
        try:
            query_handler = get_query_handler_service()
            services["query_handler"] = "healthy"
        except Exception as e:
            services["query_handler"] = f"unhealthy: {str(e)}"
        
        try:
            semantic_search = get_semantic_search_service()
            services["semantic_search"] = "healthy"
        except Exception as e:
            services["semantic_search"] = f"unhealthy: {str(e)}"
        
        try:
            disambiguation = get_disambiguation_service()
            services["disambiguation"] = "healthy"
        except Exception as e:
            services["disambiguation"] = f"unhealthy: {str(e)}"
        
        try:
            context_builder = get_context_builder_service()
            services["context_builder"] = "healthy"
        except Exception as e:
            services["context_builder"] = f"unhealthy: {str(e)}"
        
        overall_status = "healthy" if all("healthy" in status for status in services.values()) else "unhealthy"
        
        return HealthResponse(
            status=overall_status,
            services=services,
            timestamp=datetime.datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="unhealthy",
            services={"error": str(e)},
            timestamp=datetime.datetime.utcnow().isoformat()
        )


def calculate_confidence_score(response: QueryHandlerResponse) -> float:
    """
    Calculate confidence score based on search results and context.
    
    Args:
        response: Query handler response
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    if response.kb_results_count == 0:
        return 0.0
    
    # Base score on number of results and average relevance
    if response.search_results:
        # search_results are now dictionaries
        avg_score = sum(r.get("score", 0.0) for r in response.search_results) / len(response.search_results)
    else:
        avg_score = 0.0
    
    # Adjust based on context quality
    context_factor = min(response.total_tokens / 1000, 1.0)  # More context = higher confidence
    
    # Combine factors
    confidence = (avg_score * 0.7) + (context_factor * 0.3)
    
    return round(min(confidence, 1.0), 3)

def _build_context_text(context_window) -> str:
    """Build context text from context window."""
    if not context_window.chunks:
        return ""
    
    context_parts = []
    for chunk in context_window.chunks:
        # Add source information if available
        source_info = f"[{chunk.source}]"
        if chunk.section:
            source_info += f" [{chunk.section}]"
        
        context_parts.append(f"{source_info} {chunk.text}")
    
    return "\n\n".join(context_parts)
