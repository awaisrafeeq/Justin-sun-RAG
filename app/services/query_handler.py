"""
Query Handler Service for Day 12 Chat Endpoint

Orchestrates the complete query processing pipeline:
1. Embed query
2. Vector search
3. Relevance check
4. Disambiguation
5. Build context
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from app.services.query_embedding import QueryEmbeddingService
from app.services.semantic_search import SemanticSearchService, SearchRequest, SearchResponse
from app.services.disambiguation import DisambiguationService
from app.services.context_builder import ContextBuilder

logger = logging.getLogger(__name__)


@dataclass
class QueryHandlerRequest:
    """Request for query handler."""
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    max_context_tokens: int = 4000
    relevance_threshold: float = 0.7


@dataclass
class QueryHandlerResponse:
    """Response from query handler."""
    query: str
    context: str
    sources: List[Dict[str, Any]]
    needs_disambiguation: bool
    disambiguation_options: Optional[List[Dict[str, Any]]] = None
    search_results: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Response metadata
    processing_time_ms: float = 0.0
    total_tokens: int = 0
    context_sources_count: int = 0
    kb_results_count: int = 0
    web_results_count: int = 0


class QueryHandlerService:
    """
    Service that orchestrates the complete query processing pipeline.
    """
    
    def __init__(self):
        self.embedding_service = QueryEmbeddingService()
        self.semantic_search_service = SemanticSearchService()
        self.disambiguation_service = DisambiguationService()
        self.context_builder_service = ContextBuilder()
    
    async def process_query(self, request: QueryHandlerRequest) -> QueryHandlerResponse:
        """
        Process a query through the complete pipeline.
        
        Args:
            request: Query handler request
            
        Returns:
            Query handler response with context and metadata
        """
        import time
        start_time = time.time()
        
        try:
            logger.info(f"Processing query: {request.query[:100]}...")
            
            # Step 1: Embed query
            logger.info("Step 1: Embedding query...")
            query_embedding = await self.embedding_service.embed_query(request.query)
            
            # Step 2: Vector search with relevance check
            logger.info("Step 2: Performing semantic search...")
            search_request = SearchRequest(
                query=request.query,
                limit=10,
                relevance_threshold=request.relevance_threshold,
                filters=request.filters or {}
            )
            
            search_response = await self.semantic_search_service.search(search_request)
            search_results = search_response.results
            
            logger.info(f"Found {len(search_results)} search results")
            
            # Step 3: Disambiguation (if multiple entities)
            logger.info("Step 3: Checking for disambiguation...")
            entity_groups, disambiguation_options = self.disambiguation_service.disambiguate_results(
                search_results, 
                max_groups=5, 
                min_score_threshold=request.relevance_threshold
            )
            
            needs_disambiguation = disambiguation_options is not None
            
            # Step 4: Build context
            logger.info("Step 4: Building context...")
            context_window = self.context_builder_service.build_context_from_results(
                search_results,
                max_tokens=request.max_context_tokens,
                include_sources=True,
                include_sections=True,
                include_relevance=False
            )
            
            # Prepare sources list
            sources = []
            for result in search_results:
                sources.append({
                    "chunk_id": result.chunk_id,
                    "document_id": result.document_id,
                    "text_preview": result.text[:200] + "..." if len(result.text) > 200 else result.text,
                    "score": result.score,
                    "metadata": result.metadata
                })
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            # Build response
            response = QueryHandlerResponse(
                query=request.query,
                context=self._build_context_text(context_window),
                sources=sources,
                needs_disambiguation=needs_disambiguation,
                disambiguation_options=self._convert_disambiguation_options(disambiguation_options) if needs_disambiguation else None,
                search_results=self._convert_search_results(search_results),
                metadata={
                    "query_embedding_length": len(query_embedding),
                    "relevance_threshold": request.relevance_threshold,
                    "filters_applied": request.filters or {},
                    "context_truncated": len(context_window.chunks) < len(search_results),
                    "dropped_results": len(search_results) - len(context_window.chunks),
                    "entity_groups": len(entity_groups)
                },
                processing_time_ms=processing_time,
                total_tokens=context_window.total_tokens,
                context_sources_count=len(set(chunk.source for chunk in context_window.chunks)),
                kb_results_count=len(search_results),
                web_results_count=0  # Will be updated in Day 14
            )
            
            logger.info(f"Query processed in {processing_time:.2f}ms")
            logger.info(f"Context built with {response.total_tokens} tokens from {response.context_sources_count} sources")
            
            return response
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            processing_time = (time.time() - start_time) * 1000
            
            # Return error response
            return QueryHandlerResponse(
                query=request.query,
                context="",
                sources=[],
                needs_disambiguation=False,
                metadata={"error": str(e)},
                processing_time_ms=processing_time,
                total_tokens=0,
                context_sources_count=0,
                kb_results_count=0,
                web_results_count=0
            )
    
    async def get_available_filters(self) -> Dict[str, List[str]]:
        """
        Get available filter options for search.
        
        Returns:
            Dictionary of filter types and their available values
        """
        # This would typically query the database for available options
        # For now, return the static options from semantic search service
        return {
            "doc_type": ["article", "cv", "report", "other"],
            "source_type": ["pdf", "transcript", "document"],
            "section": ["abstract", "introduction", "methodology", "results", "conclusion", "experience", "education", "skills", "contact", "summary"]
        }
    
    def _build_context_text(self, context_window) -> str:
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
    
    def _convert_search_results(self, search_results):
        """Convert SearchResult objects to dictionaries."""
        results_dict = []
        for result in search_results:
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
        return results_dict
    
    def _convert_disambiguation_options(self, disambiguation_options):
        """Convert DisambiguationOption objects to dictionaries."""
        options_dict = []
        for option in disambiguation_options:
            options_dict.append({
                "group_id": option.group_id,
                "title": option.title,
                "description": option.description,
                "entity_type": option.entity_type,
                "result_count": option.result_count,
                "avg_score": option.avg_score,
                "sample_text": option.sample_text,
                "metadata": option.metadata
            })
        return options_dict
