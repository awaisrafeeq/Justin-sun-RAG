"""API schemas for semantic search."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Search request schema."""
    query: str = Field(..., description="Search query string", min_length=1, max_length=1000)
    limit: int = Field(10, description="Maximum number of results to return", ge=1, le=100)
    relevance_threshold: float = Field(0.7, description="Minimum relevance score threshold", ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")
    include_metadata: bool = Field(True, description="Include metadata in results")
    max_context_tokens: Optional[int] = Field(None, description="Maximum tokens for context building", ge=100, le=128000)


class SearchResultSchema(BaseModel):
    """Individual search result schema."""
    chunk_id: str
    document_id: str
    text: str
    metadata: Dict[str, Any]
    score: float
    document_title: Optional[str] = None
    document_type: Optional[str] = None
    section: Optional[str] = None


class SearchResponse(BaseModel):
    """Search response schema."""
    query: str
    results: List[SearchResultSchema]
    total_found: int
    relevance_threshold: float
    filters_applied: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[float] = None
    context: Optional[Dict[str, Any]] = None


class DisambiguationOptionSchema(BaseModel):
    """Disambiguation option schema."""
    group_id: str
    title: str
    description: str
    entity_type: str
    result_count: int
    avg_score: float
    sample_text: str
    metadata: Dict[str, Any]


class DisambiguationResponse(BaseModel):
    """Disambiguation response schema."""
    query: str
    needs_disambiguation: bool
    options: List[DisambiguationOptionSchema]
    processing_time_ms: Optional[float] = None


class ContextSelectionRequest(BaseModel):
    """Context selection request schema."""
    group_id: str = Field(..., description="Selected entity group ID")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for context", ge=100, le=128000)
    include_sources: bool = Field(True, description="Include source information")
    include_sections: bool = Field(True, description="Include section information")
    include_relevance: bool = Field(False, description="Include relevance scores")


class ContextResponse(BaseModel):
    """Context response schema."""
    context: str
    chunks: List[Dict[str, Any]]
    total_tokens: int
    sources: List[str]
    sections: List[str]
    metadata: Dict[str, Any]
    truncated: bool = False
    dropped_results: int = 0
