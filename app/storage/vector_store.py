from __future__ import annotations

import logging
import uuid
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from app.config import settings
from app.ingestion.chunker import Chunk

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Qdrant vector store for document and podcast chunks.
    """
    
    def __init__(self, collection_name: str = "document_chunks"):
        # Connect to Qdrant
        self.client = QdrantClient(
            host="localhost",  # Force localhost for local dev
            port=6333,
            # api_key=settings.qdrant_api_key  # Disabled for local dev
        )
        self.collection_name = collection_name
        
    async def ensure_collection(self, vector_size: int = 1536) -> None:
        """
        Ensure that Qdrant collection exists.
        """
        try:
            # Check if collection exists
            self.client.get_collection(self.collection_name)
            logger.info("Collection %s already exists", self.collection_name)
        except Exception:
            # Create collection if it doesn't exist
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info("Created collection %s with vector size %d", self.collection_name, vector_size)
    
    async def store_chunks(
        self, 
        chunks: List[Chunk], 
        embeddings: List[List[float]],
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Store chunks with their embeddings in Qdrant.
        
        Args:
            chunks: List of text chunks
            embeddings: List of embedding vectors
            document_id: Document UUID (or episode_id for podcasts)
            metadata: Additional metadata to store
            
        Returns:
            List of chunk IDs
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have same length")
        
        await self.ensure_collection(len(embeddings[0]) if embeddings else 1536)
        
        chunk_ids = []
        points = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = str(uuid.uuid4())
            chunk_ids.append(chunk_id)
            
            # Prepare point metadata
            point_metadata = {
                "document_id": document_id,
                "chunk_index": i,
                "text": chunk.text,
                "source_type": chunk.metadata.get("source_type", "document"),
            }
            
            # Add chunk-specific metadata
            if chunk.metadata:
                point_metadata.update(chunk.metadata)
            
            # Add additional metadata
            if metadata:
                point_metadata.update(metadata)
            
            point = PointStruct(
                id=chunk_id,
                vector=embedding,
                payload=point_metadata
            )
            points.append(point)
        
        # Batch insert points
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        logger.info("Stored %d chunks in Qdrant for document %s", len(chunks), document_id)
        return chunk_ids
    
    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: float = 0.7,
        document_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks.
        
        Args:
            query_embedding: Embedding of the query
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            document_filter: Optional document ID to filter by
            
        Returns:
            List of search results with metadata
        """
        # Build filter if document_id is provided
        query_filter = None
        if document_filter:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_filter)
                    )
                ]
            )
        
        # Search in Qdrant
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold
        )
        
        # Format results
        results = []
        for hit in search_result:
            results.append({
                "chunk_id": hit.id,
                "score": hit.score,
                "text": hit.payload.get("text"),
                "document_id": hit.payload.get("document_id"),
                "chunk_index": hit.payload.get("chunk_index"),
                "metadata": {
                    k: v for k, v in hit.payload.items() 
                    if k not in ["text", "document_id", "chunk_index"]
                }
            })
        
        logger.info("Found %d similar chunks for query", len(results))
        return results
    
    async def get_chunks_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all chunks for a specific document.
        """
        # Build filter for document
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id)
                )
            ]
        )
        
        # Retrieve all points for the document
        scroll_result = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=query_filter,
            limit=10000  # Adjust based on expected chunk count
        )
        
        chunks = []
        for point in scroll_result[0]:  # points are the first element
            chunks.append({
                "chunk_id": point.id,
                "text": point.payload.get("text"),
                "chunk_index": point.payload.get("chunk_index"),
                "metadata": {
                    k: v for k, v in point.payload.items() 
                    if k not in ["text", "chunk_index"]
                }
            })
        
        # Sort by chunk_index
        chunks.sort(key=lambda x: x["chunk_index"])
        
        logger.info("Retrieved %d chunks for document %s", len(chunks), document_id)
        return chunks
    
    async def delete_document_chunks(self, document_id: str) -> None:
        """
        Delete all chunks for a specific document.
        """
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id)
                )
            ]
        )
        
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=query_filter
        )
        
        logger.info("Deleted chunks for document %s", document_id)
