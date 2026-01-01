"""Context builder for assembling search results into context windows."""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import tiktoken

from app.services.semantic_search import SearchResult
from app.services.disambiguation import EntityGroup, DisambiguationOption

logger = logging.getLogger(__name__)


@dataclass
class ContextChunk:
    """Individual chunk of context with metadata."""
    text: str
    source: str
    section: Optional[str]
    chunk_id: str
    document_id: str
    relevance_score: float
    token_count: int


@dataclass
class ContextWindow:
    """Complete context window with metadata."""
    chunks: List[ContextChunk]
    total_tokens: int
    sources: List[str]
    sections: List[str]
    metadata: Dict[str, Any]
    truncated: bool = False
    dropped_results: int = 0


class ContextBuilder:
    """Service for building context windows from search results."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.model_name = model_name
        self.tokenizer = tiktoken.encoding_for_model(model_name)
        self.max_context_tokens = self._get_max_tokens_for_model(model_name)
    
    def build_context_from_results(
        self,
        results: List[SearchResult],
        max_tokens: Optional[int] = None,
        include_sources: bool = True,
        include_sections: bool = True,
        include_relevance: bool = False
    ) -> ContextWindow:
        """
        Build context window from search results.
        
        Args:
            results: List of search results
            max_tokens: Maximum tokens for context (default: model limit)
            include_sources: Whether to include source information
            include_sections: Whether to include section information
            include_relevance: Whether to include relevance scores
            
        Returns:
            Context window with assembled chunks
        """
        if not results:
            return ContextWindow(
                chunks=[],
                total_tokens=0,
                sources=[],
                sections=[],
                metadata={}
            )
        
        max_tokens = max_tokens or self.max_context_tokens
        
        # Convert results to context chunks
        context_chunks = []
        sources = set()
        sections = set()
        
        for result in results:
            # Format chunk text
            chunk_text = self._format_chunk_text(
                result,
                include_sources=include_sources,
                include_sections=include_sections,
                include_relevance=include_relevance
            )
            
            # Count tokens
            token_count = len(self.tokenizer.encode(chunk_text))
            
            # Create context chunk
            chunk = ContextChunk(
                text=chunk_text,
                source=result.document_title or f"Document {result.document_id[:8]}",
                section=result.section,
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                relevance_score=result.score,
                token_count=token_count
            )
            
            context_chunks.append(chunk)
            
            if include_sources:
                sources.add(chunk.source)
            if include_sections and chunk.section:
                sections.add(chunk.section)
        
        # Apply token limit
        final_chunks, truncated, dropped = self._apply_token_limit(
            context_chunks, max_tokens
        )
        
        # Calculate total tokens
        total_tokens = sum(chunk.token_count for chunk in final_chunks)
        
        # Build metadata
        metadata = {
            "model_name": self.model_name,
            "max_tokens": max_tokens,
            "original_result_count": len(results),
            "included_result_count": len(final_chunks),
            "average_relevance": sum(r.score for r in results) / len(results) if results else 0
        }
        
        return ContextWindow(
            chunks=final_chunks,
            total_tokens=total_tokens,
            sources=list(sources),
            sections=list(sections),
            metadata=metadata,
            truncated=truncated,
            dropped_results=dropped
        )
    
    def build_context_from_entity_group(
        self,
        entity_group: EntityGroup,
        max_tokens: Optional[int] = None,
        include_sources: bool = True,
        include_sections: bool = True,
        include_relevance: bool = False
    ) -> ContextWindow:
        """
        Build context window from a single entity group.
        
        Args:
            entity_group: Entity group with related results
            max_tokens: Maximum tokens for context
            include_sources: Whether to include source information
            include_sections: Whether to include section information
            include_relevance: Whether to include relevance scores
            
        Returns:
            Context window for the entity group
        """
        # Sort results by relevance score
        sorted_results = sorted(entity_group.results, key=lambda x: x.score, reverse=True)
        
        context = self.build_context_from_results(
            sorted_results,
            max_tokens=max_tokens,
            include_sources=include_sources,
            include_sections=include_sections,
            include_relevance=include_relevance
        )
        
        # Add entity-specific metadata
        context.metadata.update({
            "entity_id": entity_group.entity_id,
            "entity_type": entity_group.entity_type,
            "entity_title": entity_group.entity_title,
            "entity_score": entity_group.combined_score
        })
        
        return context
    
    def build_disambiguation_context(
        self,
        options: List[DisambiguationOption],
        max_tokens_per_option: int = 200
    ) -> str:
        """
        Build context for disambiguation prompt.
        
        Args:
            options: Disambiguation options
            max_tokens_per_option: Maximum tokens per option description
            
        Returns:
            Formatted disambiguation context string
        """
        context_parts = ["Multiple relevant documents found. Please select the most relevant one:\n"]
        
        for i, option in enumerate(options, 1):
            # Format option description
            option_text = f"{i}. {option.title}\n"
            option_text += f"   {option.description}\n"
            option_text += f"   Relevance: {option.avg_score:.2f}\n"
            
            if option.sample_text:
                # Truncate sample text if needed
                sample_tokens = len(self.tokenizer.encode(option.sample_text))
                if sample_tokens > max_tokens_per_option:
                    # Truncate to token limit
                    sample_tokens_list = self.tokenizer.encode(option.sample_text)
                    truncated_tokens = sample_tokens_list[:max_tokens_per_option]
                    option.sample_text = self.tokenizer.decode(truncated_tokens) + "..."
                
                option_text += f"   Preview: {option.sample_text}\n"
            
            context_parts.append(option_text)
        
        return "\n".join(context_parts)
    
    def _format_chunk_text(
        self,
        result: SearchResult,
        include_sources: bool,
        include_sections: bool,
        include_relevance: bool
    ) -> str:
        """Format individual chunk text with metadata."""
        text_parts = []
        
        # Add source information
        if include_sources:
            source = result.document_title or f"Document {result.document_id[:8]}"
            text_parts.append(f"[Source: {source}]")
        
        # Add section information
        if include_sections and result.section:
            text_parts.append(f"[Section: {result.section}]")
        
        # Add relevance score
        if include_relevance:
            text_parts.append(f"[Relevance: {result.score:.2f}]")
        
        # Add the actual text
        text_parts.append(result.text)
        
        return " ".join(text_parts)
    
    def _apply_token_limit(
        self,
        chunks: List[ContextChunk],
        max_tokens: int
    ) -> Tuple[List[ContextChunk], bool, int]:
        """
        Apply token limit to context chunks.
        
        Args:
            chunks: List of context chunks
            max_tokens: Maximum total tokens
            
        Returns:
            Tuple of (final_chunks, truncated, dropped_count)
        """
        if not chunks:
            return chunks, False, 0
        
        total_tokens = sum(chunk.token_count for chunk in chunks)
        
        if total_tokens <= max_tokens:
            return chunks, False, 0
        
        # Need to truncate chunks
        final_chunks = []
        current_tokens = 0
        dropped_count = 0
        
        for chunk in chunks:
            if current_tokens + chunk.token_count <= max_tokens:
                final_chunks.append(chunk)
                current_tokens += chunk.token_count
            else:
                dropped_count += 1
        
        return final_chunks, True, dropped_count
    
    def _get_max_tokens_for_model(self, model_name: str) -> int:
        """Get maximum context tokens for a model."""
        # Common model token limits
        model_limits = {
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-4-turbo": 128000,
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000
        }
        
        return model_limits.get(model_name, 4096)  # Default to 4096
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for a text string."""
        return len(self.tokenizer.encode(text))
    
    def truncate_text_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit."""
        tokens = self.tokenizer.encode(text)
        if len(tokens) <= max_tokens:
            return text
        
        truncated_tokens = tokens[:max_tokens]
        return self.tokenizer.decode(truncated_tokens)
