from __future__ import annotations

import io
import logging
# from docling import ...
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from functools import lru_cache

from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    text: str
    metadata: dict


class DoclingProcessor:
    """
    Thin wrapper that hides Docling configuration for both PDF documents and audio transcripts.
    """

    def __init__(
        self,
        converter: Optional[DocumentConverter] = None,
    ) -> None:
        if converter is not None:
            self.converter = converter
        else:
            self.converter = DocumentConverter()
        logger.info("Docling processor initialised")

    def process_pdf(self, file_path: str | Path) -> List[Chunk]:
        """
        Convert a PDF to text chunks with metadata.
        """
        pdf_path = Path(file_path)
        logger.info("Processing PDF via Docling: %s", pdf_path)
        result = self.converter.convert(pdf_path)

        chunks: List[Chunk] = []
        for section in result.document.sections:
            chunks.append(
                Chunk(
                    text=section.text,
                    metadata={
                        "source_type": "document",
                        "section": section.label,
                        "page_numbers": section.metadata.get("pages"),
                        "filename": pdf_path.name,
                    },
                )
            )
        logger.info("Docling produced %s chunks for %s", len(chunks), pdf_path.name)
        return chunks

    def process_audio(self, audio_bytes: bytes, *, source_url: str | None = None) -> List[Chunk]:
        """
        Convert audio (podcast episode) to transcript chunks.
        """
        logger.info("Processing audio via Docling (source=%s)", source_url)
        buffer = io.BytesIO(audio_bytes)
        result = self.converter.convert(buffer)

        chunks: List[Chunk] = []
        for idx, segment in enumerate(result.document.sections):
            chunks.append(
                Chunk(
                    text=segment.text,
                    metadata={
                        "source_type": "podcast",
                        "segment_index": idx,
                        "timestamp": segment.metadata.get("timecodes"),
                        "source_url": source_url,
                    },
                )
            )
        logger.info("Docling produced %s transcript segments", len(chunks))
        return chunks

    def process_audio_path(self, audio_path: str | Path, *, source_url: str | None = None) -> List[Chunk]:
        """
        Convert audio from a filesystem path to transcript chunks.
        """
        path = Path(audio_path)
        logger.info("Processing audio via Docling from path=%s (source=%s)", path, source_url)
        result = self.converter.convert(path)

        chunks: List[Chunk] = []
        for idx, segment in enumerate(result.document.sections):
            chunks.append(
                Chunk(
                    text=segment.text,
                    metadata={
                        "source_type": "podcast",
                        "segment_index": idx,
                        "timestamp": segment.metadata.get("timecodes"),
                        "source_url": source_url,
                        "filename": path.name,
                    },
                )
            )
        logger.info("Docling produced %s transcript segments", len(chunks))
        return chunks


def preview_chunks(chunks: Iterable[Chunk], limit: int = 3) -> None:
    for idx, chunk in enumerate(chunks):
        if idx >= limit:
            break
        logger.debug("Chunk #%s (%s chars) metadata=%s", idx, len(chunk.text), chunk.metadata)


@lru_cache(maxsize=1)
def get_docling_processor() -> DoclingProcessor:
    return DoclingProcessor()
