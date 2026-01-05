"""Pydantic schemas for content generation API."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class InterviewQuestionsRequest(BaseModel):
    """Request for interview question generation."""
    cv_content: str = Field(..., description="CV content to generate questions for", min_length=50, max_length=10000)
    context: Optional[str] = Field(None, description="Additional context from search")
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    max_tokens: int = Field(1000, description="Maximum tokens for generation", ge=100, le=2000)
    temperature: float = Field(0.7, description="Generation temperature", ge=0.0, le=2.0)


class EpisodeBriefRequest(BaseModel):
    """Request for episode brief generation."""
    transcript_content: str = Field(..., description="Podcast transcript content", min_length=100, max_length=20000)
    context: Optional[str] = Field(None, description="Additional context from search")
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    max_tokens: int = Field(1000, description="Maximum tokens for generation", ge=100, le=2000)
    temperature: float = Field(0.7, description="Generation temperature", ge=0.0, le=2.0)


class SummaryRequest(BaseModel):
    """Request for document summary generation."""
    document_content: str = Field(..., description="Document content to summarize", min_length=100, max_length=20000)
    context: Optional[str] = Field(None, description="Additional context from search")
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    max_tokens: int = Field(1000, description="Maximum tokens for generation", ge=100, le=2000)
    temperature: float = Field(0.7, description="Generation temperature", ge=0.0, le=2.0)


class GenerationResponse(BaseModel):
    """Response from content generation."""
    generated_content: str = Field(..., description="Generated content")
    generation_type: str = Field(..., description="Type of generation performed")
    tokens_used: int = Field(..., description="Tokens used for generation")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")


class GenerationOptionsResponse(BaseModel):
    """Response with available generation options."""
    generation_types: List[str] = Field(..., description="Available generation types")
    max_tokens_range: Dict[str, int] = Field(..., description="Token limits")
    temperature_range: Dict[str, float] = Field(..., description="Temperature limits")
    supported_formats: List[str] = Field(..., description="Supported input formats")


class GenerationHealthResponse(BaseModel):
    """Response from generation health check."""
    status: str = Field(..., description="Service status")
    services: Dict[str, str] = Field(..., description="Individual service statuses")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
