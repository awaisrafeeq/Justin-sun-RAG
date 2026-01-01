"""Query embedding service for semantic search."""

import logging
from typing import List, Optional

from app.storage.embeddings import EmbeddingClient

logger = logging.getLogger(__name__)


class QueryEmbeddingService:
    """Service for embedding user queries for semantic search."""
    
    def __init__(self):
        self.embedding_client = EmbeddingClient()
    
    async def embed_query(self, query: str) -> List[float]:
        """
        Embed a single query string.
        
        Args:
            query: The query string to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            embedding = await self.embedding_client.embed_query(query)
            return embedding
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise
    
    async def embed_multiple_queries(self, queries: List[str]) -> List[List[float]]:
        """
        Embed multiple query strings.
        
        Args:
            queries: List of query strings to embed
            
        Returns:
            List of embedding vectors, one per query
        """
        try:
            embeddings = await self.embedding_client.embed_documents(queries)
            return embeddings
        except Exception as e:
            logger.error(f"Failed to embed multiple queries: {e}")
            raise
    
    def normalize_query(self, query: str) -> str:
        """
        Normalize query text for better embedding results.
        
        Args:
            query: Raw query string
            
        Returns:
            Normalized query string
        """
        # Basic normalization
        query = query.strip()
        
        # Remove excessive whitespace
        query = " ".join(query.split())
        
        # Ensure query is not empty
        if not query:
            raise ValueError("Query cannot be empty")
        
        return query
