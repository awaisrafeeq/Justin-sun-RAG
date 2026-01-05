"""Generation API endpoints for content creation."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.api.schemas.generation import (
    InterviewQuestionsRequest, EpisodeBriefRequest, SummaryRequest,
    GenerationResponse, GenerationOptionsResponse, GenerationHealthResponse
)
from app.services.content_generation import ContentGenerationService, GenerationRequest, GenerationResponse as ServiceResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generate", tags=["generation"])

# Lazy loading for services
_content_generation_service = None


def get_content_generation_service() -> ContentGenerationService:
    """Get or create content generation service."""
    global _content_generation_service
    if _content_generation_service is None:
        _content_generation_service = ContentGenerationService()
    return _content_generation_service


@router.post("/interview-questions", response_model=GenerationResponse)
async def generate_interview_questions(request: InterviewQuestionsRequest) -> GenerationResponse:
    """
    Generate interview questions based on CV content.
    
    Takes CV content and generates thoughtful, relevant interview questions
    that assess technical skills, experience, and cultural fit.
    """
    try:
        logger.info(f"Generating interview questions for user: {request.user_id}")
        
        service = get_content_generation_service()
        
        # Convert API request to service request
        service_request = GenerationRequest(
            content=request.cv_content,
            context=request.context,
            user_id=request.user_id,
            session_id=request.session_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # Generate interview questions
        service_response = await service.generate_interview_questions(service_request)
        
        # Convert service response to API response
        api_response = GenerationResponse(
            generated_content=service_response.generated_content,
            generation_type=service_response.generation_type,
            tokens_used=service_response.tokens_used,
            processing_time_ms=service_response.processing_time_ms,
            metadata=service_response.metadata
        )
        
        logger.info(f"Interview questions generated successfully: {service_response.tokens_used} tokens")
        return api_response
        
    except Exception as e:
        logger.error(f"Interview questions generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Interview question generation failed: {str(e)}")


@router.post("/episode-brief", response_model=GenerationResponse)
async def generate_episode_brief(request: EpisodeBriefRequest) -> GenerationResponse:
    """
    Generate episode brief based on podcast transcript.
    
    Takes podcast transcript and creates a compelling episode brief
    with title, topics, quotes, and promotional content.
    """
    try:
        logger.info(f"Generating episode brief for user: {request.user_id}")
        
        service = get_content_generation_service()
        
        # Convert API request to service request
        service_request = GenerationRequest(
            content=request.transcript_content,
            context=request.context,
            user_id=request.user_id,
            session_id=request.session_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # Generate episode brief
        service_response = await service.generate_episode_brief(service_request)
        
        # Convert service response to API response
        api_response = GenerationResponse(
            generated_content=service_response.generated_content,
            generation_type=service_response.generation_type,
            tokens_used=service_response.tokens_used,
            processing_time_ms=service_response.processing_time_ms,
            metadata=service_response.metadata
        )
        
        logger.info(f"Episode brief generated successfully: {service_response.tokens_used} tokens")
        return api_response
        
    except Exception as e:
        logger.error(f"Episode brief generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Episode brief generation failed: {str(e)}")


@router.post("/summary", response_model=GenerationResponse)
async def generate_summary(request: SummaryRequest) -> GenerationResponse:
    """
    Generate summary based on document content.
    
    Takes document content and creates a comprehensive summary
    with key points, findings, and recommendations.
    """
    try:
        logger.info(f"Generating summary for user: {request.user_id}")
        
        service = get_content_generation_service()
        
        # Convert API request to service request
        service_request = GenerationRequest(
            content=request.document_content,
            context=request.context,
            user_id=request.user_id,
            session_id=request.session_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # Generate summary
        service_response = await service.generate_summary(service_request)
        
        # Convert service response to API response
        api_response = GenerationResponse(
            generated_content=service_response.generated_content,
            generation_type=service_response.generation_type,
            tokens_used=service_response.tokens_used,
            processing_time_ms=service_response.processing_time_ms,
            metadata=service_response.metadata
        )
        
        logger.info(f"Summary generated successfully: {service_response.tokens_used} tokens")
        return api_response
        
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@router.get("/options", response_model=GenerationOptionsResponse)
async def get_generation_options() -> GenerationOptionsResponse:
    """
    Get available generation options and limits.
    
    Returns information about supported generation types,
    token limits, and configuration options.
    """
    try:
        logger.info("Retrieving generation options")
        
        options = GenerationOptionsResponse(
            generation_types=["interview_questions", "episode_brief", "summary"],
            max_tokens_range={"min": 100, "max": 2000, "default": 1000},
            temperature_range={"min": 0.0, "max": 2.0, "default": 0.7},
            supported_formats=["text/plain", "text/markdown", "application/pdf"]
        )
        
        logger.info("Generation options retrieved successfully")
        return options
        
    except Exception as e:
        logger.error(f"Options retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Options retrieval failed: {str(e)}")


@router.get("/health", response_model=GenerationHealthResponse)
async def health_check() -> GenerationHealthResponse:
    """
    Check health of generation services.
    
    Returns status of content generation service and
    dependencies (OpenAI, embedding service).
    """
    import datetime
    services = {}
    
    try:
        # Check content generation service
        service = get_content_generation_service()
        services["content_generation"] = "healthy"
    except Exception as e:
        services["content_generation"] = f"unhealthy: {str(e)}"
    
    try:
        # Check OpenAI client
        from app.config import settings
        import openai
        if settings.openai_api_key:
            client = openai.OpenAI(api_key=settings.openai_api_key)
            client.models.list()  # Simple test call
            services["openai"] = "healthy"
        else:
            services["openai"] = "unhealthy: OPENAI_API_KEY not set"
    except Exception as e:
        services["openai"] = f"unhealthy: {str(e)}"
    
    try:
        # Check embedding service
        from app.storage.embeddings import EmbeddingClient
        embedding_client = EmbeddingClient()
        services["embedding_service"] = "healthy"
    except Exception as e:
        services["embedding_service"] = f"unhealthy: {str(e)}"
    
    # Determine overall status
    all_healthy = all("healthy" in status for status in services.values())
    overall_status = "healthy" if all_healthy else "unhealthy"
    
    return GenerationHealthResponse(
        status=overall_status,
        services=services,
        timestamp=datetime.datetime.utcnow()
    )


def calculate_generation_confidence(response: GenerationResponse) -> float:
    """
    Calculate confidence score based on generation quality metrics.
    
    Args:
        response: Generation response
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    # Base confidence on content length and processing time
    content_factor = min(len(response.generated_content) / 500, 1.0)  # More content = higher confidence
    time_factor = max(0.5, 1.0 - (response.processing_time_ms / 10000))  # Faster = higher confidence
    
    # Check for errors in metadata
    error_penalty = 0.3 if "error" in response.metadata else 0.0
    
    # Combine factors
    confidence = (content_factor * 0.4) + (time_factor * 0.3) + ((1.0 - error_penalty) * 0.3)
    
    return round(min(confidence, 1.0), 3)
