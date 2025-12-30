from __future__ import annotations

import logging
from typing import List, Dict, Any

from app.storage.embeddings import EmbeddingClient
from app.ingestion.chunker import Chunk

logger = logging.getLogger(__name__)


class EmbeddingProcessor:
    """
    Process chunks to generate embeddings in batches.
    """
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.embedding_client = EmbeddingClient()
    
    async def process_chunks(
        self, 
        chunks: List[Chunk]
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of chunks.
        
        Args:
            chunks: List of text chunks
            
        Returns:
            List of embedding vectors
        """
        if not chunks:
            return []
        
        # Extract text from chunks
        texts = [chunk.text for chunk in chunks if chunk.text]
        
        if not texts:
            logger.warning("No valid text found in chunks")
            return []
        
        logger.info(
            "Generating embeddings for %d chunks (batch size: %d)",
            len(texts),
            self.batch_size
        )
        
        # Generate embeddings in batches
        all_embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            
            try:
                batch_embeddings = await self.embedding_client.embed_documents(batch_texts)
                all_embeddings.extend(batch_embeddings)
                
                logger.info(
                    "Generated embeddings for batch %d-%d/%d",
                    i + 1,
                    min(i + self.batch_size, len(texts)),
                    len(texts)
                )
            except Exception as e:
                logger.error(
                    "Failed to generate embeddings for batch %d-%d: %s",
                    i + 1,
                    min(i + self.batch_size, len(texts)),
                    e
                )
                # Add empty embeddings to maintain alignment
                all_embeddings.extend([[0.0] * 1536] * len(batch_texts))
        
        logger.info("Generated %d total embeddings", len(all_embeddings))
        return all_embeddings
    
    async def process_single_chunk(self, chunk: Chunk) -> List[float]:
        """
        Generate embedding for a single chunk.
        
        Args:
            chunk: Single text chunk
            
        Returns:
            Embedding vector
        """
        if not chunk.text:
            logger.warning("Empty chunk text, returning zero embedding")
            return [0.0] * 1536
        
        try:
            embedding = await self.embedding_client.embed_query(chunk.text)
            logger.debug("Generated embedding for chunk: %s", chunk.text[:50])
            return embedding
        except Exception as e:
            logger.error("Failed to generate embedding for chunk: %s", e)
            return [0.0] * 1536
