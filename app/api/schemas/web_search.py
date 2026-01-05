"""Pydantic schemas for web search API."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class WebSearchRequest(BaseModel):
    """Request for web search."""
    query: str = Field(..., description="Search query", min_length=1, max_length=1000)
    max_results: int = Field(5, description="Maximum results to return", ge=1, le=20)
    search_depth: str = Field("basic", description="Search depth", enum=["basic", "advanced"])
    include_domains: Optional[List[str]] = Field(None, description="Domains to include in search")
    exclude_domains: Optional[List[str]] = Field(None, description="Domains to exclude from search")


class WebSearchResult(BaseModel):
    """Result from web search."""
    title: str = Field(..., description="Result title")
    url: str = Field(..., description="Result URL")
    content: str = Field(..., description="Result content")
    snippet: str = Field(..., description="Result snippet")
    source: str = Field(..., description="Source domain")
    relevance_score: float = Field(..., description="Relevance score", ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WebSearchResponse(BaseModel):
    """Response from web search."""
    query: str = Field(..., description="Search query")
    results: List[WebSearchResult] = Field(..., description="Search results")
    total_found: int = Field(..., description="Total results found")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Search timestamp")


class HybridSearchRequest(BaseModel):
    """Request for hybrid search (KB + Web)."""
    query: str = Field(..., description="Search query", min_length=1, max_length=1000)
    kb_confidence_threshold: float = Field(0.5, description="KB confidence threshold for fallback", ge=0.0, le=1.0)
    max_kb_results: int = Field(5, description="Maximum KB results", ge=1, le=20)
    max_web_results: int = Field(5, description="Maximum web results", ge=0, le=20)
    use_web_fallback: bool = Field(True, description="Enable web search fallback")
    search_depth: str = Field("basic", description="Web search depth", enum=["basic", "advanced"])


class HybridSearchResult(BaseModel):
    """Result from hybrid search."""
    source_type: str = Field(..., description="Source type: 'knowledge_base' or 'web'")
    title: str = Field(..., description="Result title")
    content: str = Field(..., description="Result content")
    url: Optional[str] = Field(None, description="Result URL (for web results)")
    source: str = Field(..., description="Source name/domain")
    relevance_score: float = Field(..., description="Relevance score", ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class HybridSearchResponse(BaseModel):
    """Response from hybrid search."""
    query: str = Field(..., description="Search query")
    kb_results: List[HybridSearchResult] = Field(..., description="Knowledge base results")
    web_results: List[HybridSearchResult] = Field(..., description="Web search results")
    total_kb_results: int = Field(..., description="Total KB results")
    total_web_results: int = Field(..., description="Total web results")
    used_web_fallback: bool = Field(..., description="Whether web fallback was used")
    kb_confidence_score: float = Field(..., description="KB confidence score", ge=0.0, le=1.0)
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Search timestamp")


class WebSearchOptionsResponse(BaseModel):
    """Response with web search options."""
    search_depths: List[str] = Field(..., description="Available search depths")
    max_results_range: Dict[str, int] = Field(..., description="Results limits")
    confidence_threshold_range: Dict[str, float] = Field(..., description="Confidence threshold limits")
    fallback_enabled: bool = Field(..., description="Whether web fallback is enabled")


class WebSearchHealthResponse(BaseModel):
    """Response from web search health check."""
    status: str = Field(..., description="Service status")
    services: Dict[str, str] = Field(..., description="Individual service statuses")
    api_key_configured: bool = Field(..., description="Whether Tavily API key is configured")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
