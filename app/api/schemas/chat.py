"""
API schemas for Day 12 Chat and Search endpoints.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    query: str = Field(..., description="User query", min_length=1, max_length=1000)
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    max_context_tokens: int = Field(4000, description="Maximum tokens for context", ge=1000, le=8000)
    relevance_threshold: float = Field(0.7, description="Minimum relevance score", ge=0.0, le=1.0)


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    query: str
    context: str
    sources: List[Dict[str, Any]]
    needs_disambiguation: bool
    disambiguation_options: Optional[List[Dict[str, Any]]] = None
    search_results: Optional[List[Dict[str, Any]]] = None
    
    # Response metadata
    processing_time_ms: float
    total_tokens: int
    context_sources_count: int
    kb_results_count: int
    web_results_count: int
    
    # Source attribution
    response_type: str = "knowledge_base"  # Will be "knowledge_base" or "web" in Day 14
    confidence_score: Optional[float] = None


class SearchRequest(BaseModel):
    """Request for search endpoint."""
    query: str = Field(..., description="Search query", min_length=1, max_length=1000)
    limit: int = Field(10, description="Maximum results", ge=1, le=50)
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    relevance_threshold: float = Field(0.7, description="Minimum relevance score", ge=0.0, le=1.0)
    include_context: bool = Field(False, description="Include context in response")
    max_context_tokens: int = Field(4000, description="Maximum tokens for context", ge=1000, le=8000)


class SearchResponse(BaseModel):
    """Response from search endpoint."""
    query: str
    results: List[Dict[str, Any]]
    total_found: int
    processing_time_ms: float
    
    # Context (if requested)
    context: Optional[str] = None
    context_sources: Optional[List[str]] = None
    context_tokens: Optional[int] = None
    
    # Search metadata
    filters_applied: Optional[Dict[str, Any]] = None
    relevance_threshold: float
    needs_disambiguation: bool = False
    disambiguation_options: Optional[List[Dict[str, Any]]] = None


class FilterOptionsResponse(BaseModel):
    """Response for filter options endpoint."""
    doc_type: List[str]
    source_type: List[str]
    section: List[str]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    services: Dict[str, str]
    timestamp: str
