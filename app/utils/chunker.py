from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class TextChunk:
    text: str
    metadata: dict


def sliding_window_chunk(
    text: str,
    *,
    chunk_size: int = 600,
    overlap: int = 100,
    metadata: dict | None = None,
) -> List[TextChunk]:
    """Simple tokenizer-agnostic chunking with overlap."""
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    payload = metadata or {}
    chunks: List[TextChunk] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(
                TextChunk(
                    text=chunk_text,
                    metadata={**payload, "chunk_index": len(chunks)},
                )
            )
        start += chunk_size - overlap
    return chunks


def chunk_from_docling_sections(sections: Iterable[dict], *, overlap: int = 50) -> List[TextChunk]:
    chunks: List[TextChunk] = []
    for section in sections:
        section_text = section.get("text", "")
        chunked = sliding_window_chunk(section_text, chunk_size=700, overlap=overlap, metadata=section.get("metadata", {}))
        chunks.extend(chunked)
    return chunks
