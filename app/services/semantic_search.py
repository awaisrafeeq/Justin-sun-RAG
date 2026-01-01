"""Semantic search service with relevance filtering and metadata filters."""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from app.services.query_embedding import QueryEmbeddingService
from app.storage.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Individual search result with metadata."""
    chunk_id: str
    document_id: str
    text: str
    metadata: Dict[str, Any]
    score: float
    document_title: Optional[str] = None
    document_type: Optional[str] = None
    section: Optional[str] = None


@dataclass
class SearchRequest:
    """Search request parameters."""
    query: str
    limit: int = 10
    relevance_threshold: float = 0.7
    filters: Optional[Dict[str, Any]] = None
    include_metadata: bool = True


@dataclass
class SearchResponse:
    """Search response with results and metadata."""
    query: str
    results: List[SearchResult]
    total_found: int
    relevance_threshold: float
    filters_applied: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[float] = None


class SemanticSearchService:
    """Service for semantic search with relevance filtering and metadata filters."""
    
    def __init__(self):
        self.embedding_service = QueryEmbeddingService()
        self.vector_store = VectorStore()
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Perform semantic search with relevance filtering and metadata filters.
        
        Args:
            request: Search request with query, filters, and parameters
            
        Returns:
            Search response with filtered results
        """
        import time
        start_time = time.time()
        
        try:
            # Normalize and embed query
            normalized_query = self.embedding_service.normalize_query(request.query)
            query_embedding = await self.embedding_service.embed_query(normalized_query)
            
            # Extract document_id filter if present
            document_filter = None
            if request.filters and "document_id" in request.filters:
                doc_ids = request.filters["document_id"]
                if isinstance(doc_ids, list) and len(doc_ids) > 0:
                    document_filter = doc_ids[0]  # Take first document_id for now
                elif isinstance(doc_ids, str):
                    document_filter = doc_ids
            
            # Search in vector store using embeddings
            vector_results = await self.vector_store.search_similar(
                query_embedding=query_embedding,  # Pass embedding
                limit=request.limit * 2,  # Get more results for filtering
                score_threshold=request.relevance_threshold,
                document_filter=document_filter
            )
            
            # Convert to SearchResult objects and apply additional filtering
            search_results = self._process_search_results(vector_results, request)
            
            # Apply relevance threshold filtering
            filtered_results = [
                result for result in search_results 
                if result.score >= request.relevance_threshold
            ]
            
            # Limit results
            final_results = filtered_results[:request.limit]
            
            processing_time = (time.time() - start_time) * 1000
            
            return SearchResponse(
                query=request.query,
                results=final_results,
                total_found=len(final_results),
                relevance_threshold=request.relevance_threshold,
                filters_applied=request.filters,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise
    
    def _build_qdrant_filter(self, filters: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Build Qdrant filter from metadata filters.
        
        Args:
            filters: Metadata filters dictionary
            
        Returns:
            Qdrant filter condition
        """
        if not filters:
            return None
        
        must_conditions = []
        
        # Handle document type filter
        if "doc_type" in filters:
            doc_types = filters["doc_type"]
            if isinstance(doc_types, str):
                doc_types = [doc_types]
            must_conditions.append({
                "key": "metadata.doc_type",
                "match": {"any": doc_types}
            })
        
        # Handle source type filter
        if "source_type" in filters:
            source_types = filters["source_type"]
            if isinstance(source_types, str):
                source_types = [source_types]
            must_conditions.append({
                "key": "metadata.source_type",
                "match": {"any": source_types}
            })
        
        # Handle document ID filter
        if "document_id" in filters:
            document_ids = filters["document_id"]
            if isinstance(document_ids, str):
                document_ids = [document_ids]
            must_conditions.append({
                "key": "document_id",
                "match": {"any": document_ids}
            })
        
        # Handle section filter
        if "section" in filters:
            sections = filters["section"]
            if isinstance(sections, str):
                sections = [sections]
            must_conditions.append({
                "key": "metadata.section",
                "match": {"any": sections}
            })
        
        # Handle custom metadata filters
        for key, value in filters.items():
            if key not in ["doc_type", "source_type", "document_id", "section"]:
                if isinstance(value, list):
                    must_conditions.append({
                        "key": f"metadata.{key}",
                        "match": {"any": value}
                    })
                else:
                    must_conditions.append({
                        "key": f"metadata.{key}",
                        "match": {"value": value}
                    })
        
        return {"must": must_conditions} if must_conditions else None
    
    def _process_search_results(
        self, 
        vector_results: List[Dict[str, Any]], 
        request: SearchRequest
    ) -> List[SearchResult]:
        """
        Process vector search results into SearchResult objects.
        
        Args:
            vector_results: Raw results from vector store
            request: Original search request
            
        Returns:
            List of processed search results
        """
        search_results = []
        
        for result in vector_results:
            # Extract basic information from VectorStore format
            chunk_id = result.get("chunk_id")
            text = result.get("text", "")
            score = result.get("score", 0.0)
            metadata = result.get("metadata", {})
            document_id = result.get("document_id", "")
            
            # Extract document information from metadata
            document_title = metadata.get("original_filename") or metadata.get("filename")
            document_type = metadata.get("doc_type")
            section = metadata.get("section")
            
            search_result = SearchResult(
                chunk_id=chunk_id,
                document_id=document_id,
                text=text,
                metadata=metadata if request.include_metadata else {},
                score=score,
                document_title=document_title,
                document_type=document_type,
                section=section
            )
            
            search_results.append(search_result)
        
        return search_results
