"""Search API endpoints for semantic search and disambiguation."""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.api.schemas.search import (
    SearchRequest, SearchResponse, SearchResultSchema,
    DisambiguationResponse, DisambiguationOptionSchema,
    ContextSelectionRequest, ContextResponse
)
from app.services.semantic_search import (
    SemanticSearchService, SearchRequest as SearchServiceRequest,
    SearchResponse as SearchServiceResponse, SearchResult
)
from app.services.disambiguation import (
    DisambiguationService, EntityGroup, DisambiguationOption
)
from app.services.context_builder import ContextBuilder, ContextWindow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])

# Lazy-loaded services to prevent startup hanging
def get_search_service():
    return SemanticSearchService()

def get_disambiguation_service():
    return DisambiguationService()

def get_context_builder():
    return ContextBuilder()


@router.post("/", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Perform semantic search across documents with relevance filtering and metadata filters.
    
    Args:
        request: Search request with query, filters, and parameters
        
    Returns:
        Search response with filtered results and context
    """
    try:
        # Get services lazily
        search_service = get_search_service()
        context_builder = get_context_builder()
        
        # Convert API request to service request
        service_request = SearchServiceRequest(
            query=request.query,
            limit=request.limit,
            relevance_threshold=request.relevance_threshold,
            filters=request.filters,
            include_metadata=request.include_metadata
        )
        
        # Perform search
        search_response = await search_service.search(service_request)
        
        # Convert service results to API schema
        results = [
            SearchResultSchema(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                text=result.text,
                metadata=result.metadata,
                score=result.score,
                document_title=result.document_title,
                document_type=result.document_type,
                section=result.section
            )
            for result in search_response.results
        ]
        
        # Build context if requested
        context_data = None
        if request.max_context_tokens:
            context_window = context_builder.build_context_from_results(
                search_response.results,
                max_tokens=request.max_context_tokens
            )
            context_data = {
                "chunks": [
                    {
                        "text": chunk.text,
                        "source": chunk.source,
                        "section": chunk.section,
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.document_id,
                        "relevance_score": chunk.relevance_score,
                        "token_count": chunk.token_count
                    }
                    for chunk in context_window.chunks
                ],
                "total_tokens": context_window.total_tokens,
                "sources": context_window.sources,
                "sections": context_window.sections,
                "metadata": context_window.metadata,
                "truncated": context_window.truncated,
                "dropped_results": context_window.dropped_results
            }
        
        return SearchResponse(
            query=search_response.query,
            results=results,
            total_found=search_response.total_found,
            relevance_threshold=search_response.relevance_threshold,
            filters_applied=search_response.filters_applied,
            processing_time_ms=search_response.processing_time_ms,
            context=context_data
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search service unavailable")


@router.post("/disambiguate", response_model=DisambiguationResponse)
async def disambiguate_search(request: SearchRequest):
    """
    Perform search with disambiguation for multiple entities.
    
    Args:
        request: Search request
        
    Returns:
        Disambiguation response with options if multiple entities found
    """
    try:
        # Get services lazily
        search_service = get_search_service()
        disambiguation_service = get_disambiguation_service()
        
        # Perform search first
        service_request = SearchServiceRequest(
            query=request.query,
            limit=request.limit * 2,  # Get more results for disambiguation
            relevance_threshold=request.relevance_threshold * 0.8,  # Lower threshold for more options
            filters=request.filters,
            include_metadata=True
        )
        
        search_response = await search_service.search(service_request)
        
        # Disambiguate results
        entity_groups, disambiguation_options = disambiguation_service.disambiguate_results(
            search_response.results
        )
        
        # Convert to API schema
        options_schema = []
        if disambiguation_options:
            options_schema = [
                DisambiguationOptionSchema(
                    group_id=option.group_id,
                    title=option.title,
                    description=option.description,
                    entity_type=option.entity_type,
                    result_count=option.result_count,
                    avg_score=option.avg_score,
                    sample_text=option.sample_text,
                    metadata=option.metadata
                )
                for option in disambiguation_options
            ]
        
        return DisambiguationResponse(
            query=request.query,
            needs_disambiguation=disambiguation_options is not None,
            options=options_schema,
            processing_time_ms=search_response.processing_time_ms
        )
        
    except Exception as e:
        logger.error(f"Disambiguation failed: {e}")
        raise HTTPException(status_code=500, detail="Disambiguation service unavailable")


@router.post("/context", response_model=ContextResponse)
async def build_context(request: ContextSelectionRequest):
    """
    Build context from a selected entity group.
    
    Args:
        request: Context selection request with group ID
        
    Returns:
        Context response with assembled context window
    """
    try:
        # Get services lazily
        search_service = get_search_service()
        disambiguation_service = get_disambiguation_service()
        context_builder = get_context_builder()
        
        # First, perform a search to get the entity groups
        # This is a simplified approach - in practice, you might store the disambiguation state
        service_request = SearchServiceRequest(
            query="",  # Empty query to get all results (you'd normally store this from previous search)
            limit=100,
            relevance_threshold=0.5,
            include_metadata=True
        )
        
        # For now, we'll need to search by document_id if provided in filters
        # This is a limitation of the current stateless approach
        # In a real implementation, you'd store the disambiguation state in a session or cache
        
        # Extract document_id from group_id (assuming format: "document_id" or "document_id_section")
        document_id = request.group_id.split("_")[0] if "_" in request.group_id else request.group_id
        
        # Search for specific document
        service_request.filters = {"document_id": document_id}
        search_response = await search_service.search(service_request)
        
        # Disambiguate to get entity groups
        entity_groups, _ = disambiguation_service.disambiguate_results(
            search_response.results
        )
        
        # Find the selected group
        selected_group = disambiguation_service.select_entity_group(
            entity_groups, request.group_id
        )
        
        if not selected_group:
            raise HTTPException(status_code=404, detail="Entity group not found")
        
        # Build context
        context_window = context_builder.build_context_from_entity_group(
            selected_group,
            max_tokens=request.max_tokens,
            include_sources=request.include_sources,
            include_sections=request.include_sections,
            include_relevance=request.include_relevance
        )
        
        # Combine chunks into context text
        context_text = "\n\n".join(chunk.text for chunk in context_window.chunks)
        
        return ContextResponse(
            context=context_text,
            chunks=[
                {
                    "text": chunk.text,
                    "source": chunk.source,
                    "section": chunk.section,
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "relevance_score": chunk.relevance_score,
                    "token_count": chunk.token_count
                }
                for chunk in context_window.chunks
            ],
            total_tokens=context_window.total_tokens,
            sources=context_window.sources,
            sections=context_window.sections,
            metadata=context_window.metadata,
            truncated=context_window.truncated,
            dropped_results=context_window.dropped_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Context building failed: {e}")
        raise HTTPException(status_code=500, detail="Context building service unavailable")


@router.get("/filters")
async def get_available_filters():
    """
    Get available filter options for search.
    
    Returns:
        Available filter fields and their possible values
    """
    try:
        # This would typically query your database/vector store for available options
        # For now, return static examples
        
        return {
            "doc_type": ["article", "cv", "report", "other"],
            "source_type": ["pdf", "transcript", "document"],
            "section": ["introduction", "methods", "results", "conclusion", "general"],
            "metadata_fields": [
                "doc_type",
                "source_type", 
                "document_id",
                "section",
                "extracted_name",
                "filename",
                "original_filename"
            ]
        }
        
    except Exception as e:
        logger.error(f"Getting filters failed: {e}")
        raise HTTPException(status_code=500, detail="Filter service unavailable")
