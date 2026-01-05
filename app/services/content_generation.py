"""Content generation service for various document types."""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import openai
from app.storage.embeddings import EmbeddingClient
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class GenerationRequest:
    """Base request for content generation."""
    content: str  # Source content (CV, podcast transcript, etc.)
    context: Optional[str] = None  # Additional context from search
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7


@dataclass
class GenerationResponse:
    """Response from content generation."""
    generated_content: str
    generation_type: str
    tokens_used: int
    processing_time_ms: float
    metadata: Dict[str, Any]


class ContentGenerationService:
    """
    Service for generating content based on source documents.
    
    Supports:
    - Interview questions (CVs)
    - Episode briefs (podcasts)
    - Summaries (documents)
    """
    
    def __init__(self):
        self.embedding_client = EmbeddingClient()
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def generate_interview_questions(
        self, 
        request: GenerationRequest
    ) -> GenerationResponse:
        """
        Generate interview questions based on CV content.
        
        Args:
            request: Generation request with CV content
            
        Returns:
            Generated interview questions with metadata
        """
        import time
        start_time = time.time()
        
        try:
            prompt = self._build_interview_prompt(request.content, request.context)
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert interviewer who creates thoughtful, relevant interview questions based on a candidate's CV and experience."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            generated_content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            processing_time = (time.time() - start_time) * 1000
            
            return GenerationResponse(
                generated_content=generated_content,
                generation_type="interview_questions",
                tokens_used=tokens_used,
                processing_time_ms=processing_time,
                metadata={
                    "model": "gpt-3.5-turbo",
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "has_context": request.context is not None
                }
            )
            
        except Exception as e:
            logger.error(f"Interview question generation failed: {e}")
            return GenerationResponse(
                generated_content="",
                generation_type="interview_questions",
                tokens_used=0,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)}
            )
    
    async def generate_episode_brief(
        self, 
        request: GenerationRequest
    ) -> GenerationResponse:
        """
        Generate episode brief based on podcast transcript.
        
        Args:
            request: Generation request with podcast content
            
        Returns:
            Generated episode brief with metadata
        """
        import time
        start_time = time.time()
        
        try:
            prompt = self._build_episode_prompt(request.content, request.context)
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert podcast producer who creates compelling, concise episode briefs based on podcast transcripts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            generated_content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            processing_time = (time.time() - start_time) * 1000
            
            return GenerationResponse(
                generated_content=generated_content,
                generation_type="episode_brief",
                tokens_used=tokens_used,
                processing_time_ms=processing_time,
                metadata={
                    "model": "gpt-3.5-turbo",
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "has_context": request.context is not None
                }
            )
            
        except Exception as e:
            logger.error(f"Episode brief generation failed: {e}")
            return GenerationResponse(
                generated_content="",
                generation_type="episode_brief",
                tokens_used=0,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)}
            )
    
    async def generate_summary(
        self, 
        request: GenerationRequest
    ) -> GenerationResponse:
        """
        Generate summary based on document content.
        
        Args:
            request: Generation request with document content
            
        Returns:
            Generated summary with metadata
        """
        import time
        start_time = time.time()
        
        try:
            prompt = self._build_summary_prompt(request.content, request.context)
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert content analyst who creates clear, concise summaries of documents while preserving key information and insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            generated_content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            processing_time = (time.time() - start_time) * 1000
            
            return GenerationResponse(
                generated_content=generated_content,
                generation_type="summary",
                tokens_used=tokens_used,
                processing_time_ms=processing_time,
                metadata={
                    "model": "gpt-3.5-turbo",
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "has_context": request.context is not None
                }
            )
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return GenerationResponse(
                generated_content="",
                generation_type="summary",
                tokens_used=0,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)}
            )
    
    def _build_interview_prompt(self, cv_content: str, context: Optional[str] = None) -> str:
        """Build prompt for interview question generation."""
        base_prompt = f"""You are an expert hiring manager and interviewer with 15+ years of experience conducting technical and behavioral interviews. Your task is to create insightful interview questions based on the candidate's CV.

INSTRUCTIONS:
1. Analyze the CV thoroughly to understand the candidate's experience level, skills, and career trajectory
2. Generate 8-10 high-quality interview questions that assess multiple dimensions
3. Each question should be open-ended and designed to elicit detailed, behavioral responses
4. Include a mix of technical, behavioral, and situational questions
5. For each question, briefly explain what competency or skill it assesses

CV Content:
{cv_content}

QUESTION CATEGORIES TO COVER:
- Technical Skills & Problem Solving
- Leadership & Team Collaboration  
- Communication & Interpersonal Skills
- Career Growth & Learning Mindset
- Cultural Fit & Motivation
- Project Management & Execution

OUTPUT FORMAT:
Number each question (1, 2, 3...) followed by:
- The question itself
- [Assesses: X, Y, Z] - brief explanation of what it evaluates

EXAMPLE FORMAT:
1. Describe a complex technical challenge you faced in your previous role and walk me through your problem-solving approach. [Assesses: Technical problem-solving, analytical thinking, communication under pressure]

Make questions specific to the candidate's actual experience mentioned in the CV, not generic questions."""

        if context:
            base_prompt += f"""

ADDITIONAL CONTEXT:
{context}

Use this context to tailor questions specifically for this role/opportunity. Focus on skills and experiences most relevant to the position requirements."""

        return base_prompt
    
    def _build_episode_prompt(self, transcript_content: str, context: Optional[str] = None) -> str:
        """Build prompt for episode brief generation."""
        base_prompt = f"""You are an expert podcast producer and content strategist with extensive experience in creating compelling episode briefs that drive engagement and audience growth. Your task is to analyze the podcast transcript and create a comprehensive brief.

INSTRUCTIONS:
1. Carefully analyze the entire transcript to identify key themes, insights, and memorable moments
2. Create content that will resonate with the target audience and drive engagement
3. Focus on actionable insights and compelling storytelling elements
4. Ensure all content is accurate and properly represents the discussion

Transcript Content:
{transcript_content}

REQUIRED ELEMENTS:

1. EPISODE TITLE
- Catchy, descriptive, and SEO-friendly
- 5-10 words maximum
- Should clearly indicate the main topic

2. KEY TOPICS DISCUSSED
- 3-5 main themes covered
- Each topic: 1-2 sentences explaining what was discussed
- Include any surprising or controversial points

3. NOTABLE QUOTES/MOMENTS
- 2-3 most memorable quotes or insights
- Include speaker attribution if possible
- Explain why each quote/moment is significant

4. TARGET AUDIENCE
- Who would benefit most from this episode?
- Specific demographics or professional groups
- Pain points or interests addressed

5. EPISODE DESCRIPTION
- 2-3 compelling sentences for promotion
- Hook listeners and highlight key takeaways
- Include call-to-action if relevant

6. SOCIAL MEDIA HOOKS
- 3-4 shareable points for Twitter/LinkedIn
- Each hook: 1-2 sentences maximum
- Include relevant hashtags if applicable

OUTPUT FORMAT:
Use clear headings for each section. Make the brief engaging, professional, and ready for immediate use in promotion and distribution."""

        if context:
            base_prompt += f"""

ADDITIONAL CONTEXT:
{context}

Use this context to emphasize topics most relevant to current trends, audience interests, or promotional opportunities. Tailor the content to align with the broader content strategy."""

        return base_prompt
    
    def _build_summary_prompt(self, document_content: str, context: Optional[str] = None) -> str:
        """Build prompt for document summarization."""
        base_prompt = f"""You are an expert content analyst and research strategist with extensive experience in creating comprehensive, actionable summaries for various audiences including executives, researchers, and practitioners. Your task is to analyze the document and create a structured summary that preserves key insights while making the content accessible.

INSTRUCTIONS:
1. Read and comprehend the entire document thoroughly
2. Identify the core message, key findings, and practical implications
3. Structure the summary for maximum clarity and usability
4. Maintain accuracy and proper attribution of ideas
5. Focus on actionable insights and practical takeaways

Document Content:
{document_content}

REQUIRED ELEMENTS:

1. EXECUTIVE SUMMARY
- 2-3 sentences capturing the essence of the document
- Include the main conclusion or recommendation
- Written for busy decision-makers who need the key takeaway immediately

2. KEY POINTS
- 5-7 bullet points highlighting the most important information
- Each point should be concise yet comprehensive
- Include data, statistics, or specific findings where available

3. MAIN ARGUMENTS/FINDINGS
- 3-4 key arguments or research findings
- Each point: 2-3 sentences explaining the finding and its significance
- Include methodology or evidence basis if relevant

4. IMPLICATIONS/RECOMMENDATIONS
- 2-3 practical implications or actionable recommendations
- Focus on what the reader should do or consider based on this information
- Include potential next steps or areas for further investigation

5. TARGET AUDIENCE & USE CASES
- Who would benefit most from this document?
- Specific scenarios or decisions where this information is valuable
- How different stakeholders might use these insights

QUALITY STANDARDS:
- Clear, concise, and professional language
- Accurate representation of the source material
- Well-structured for easy scanning and reference
- Informative without unnecessary jargon or detail
- Actionable insights that drive decision-making

OUTPUT FORMAT:
Use clear headings and bullet points for readability. Ensure the summary stands alone while accurately representing the full document."""

        if context:
            base_prompt += f"""

ADDITIONAL CONTEXT:
{context}

Use this context to emphasize aspects most relevant to the reader's specific needs, interests, or decision-making requirements. Tailor the summary to address the most pressing questions or concerns the reader might have."""

        return base_prompt
