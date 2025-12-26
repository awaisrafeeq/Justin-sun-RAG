from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, Sequence

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "text-embedding-3-small"


@dataclass
class EmbeddingResult:
    vector: Sequence[float]
    metadata: dict


class EmbeddingClient:
    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY missing; set it in .env before embedding.")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = model
        logger.info("Embedding client ready (model=%s)", model)

    async def embed_documents(self, texts: Iterable[str]) -> list[list[float]]:
        batched_texts = list(texts)
        if not batched_texts:
            return []

        logger.debug("Embedding %s documents", len(batched_texts))
        response = await self.client.embeddings.create(model=self.model, input=batched_texts)
        return [record.embedding for record in response.data]

    async def embed_query(self, query: str) -> list[float]:
        response = await self.client.embeddings.create(model=self.model, input=query)
        return response.data[0].embedding
