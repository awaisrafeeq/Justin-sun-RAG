from __future__ import annotations

import logging
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

MAX_DOWNLOAD_SIZE = 200 * 1024 * 1024  # 200 MB safeguard


class AudioDownloadError(Exception):
    pass


def download_audio(url: str, *, timeout: float = 60.0) -> bytes:
    """
    Stream an audio file into memory with a safety limit.
    """
    logger.info("Downloading audio from %s", url)
    with httpx.stream("GET", url, timeout=timeout, follow_redirects=True) as response:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("Failed to download audio (%s): %s", url, exc)
            raise AudioDownloadError(str(exc)) from exc

        chunks = []
        downloaded = 0
        for chunk in response.iter_bytes(chunk_size=1024 * 1024):
            if not chunk:
                continue
            downloaded += len(chunk)
            if downloaded > MAX_DOWNLOAD_SIZE:
                raise AudioDownloadError("Audio file exceeds max download size")
            chunks.append(chunk)
        audio_bytes = b"".join(chunks)
        logger.info("Downloaded %s bytes from %s", len(audio_bytes), url)
        return audio_bytes


@contextmanager
def download_audio_to_tempfile(url: str, *, timeout: float = 60.0, suffix: str = ".audio"):
    """
    Stream an audio file to a temp file with a safety limit.

    Yields a filesystem path and ensures cleanup.
    """
    logger.info("Downloading audio to temp file from %s", url)
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name

            with httpx.stream("GET", url, timeout=timeout, follow_redirects=True) as response:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    logger.error("Failed to download audio (%s): %s", url, exc)
                    raise AudioDownloadError(str(exc)) from exc

                downloaded = 0
                for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    downloaded += len(chunk)
                    if downloaded > MAX_DOWNLOAD_SIZE:
                        raise AudioDownloadError("Audio file exceeds max download size")
                    tmp.write(chunk)

        yield Path(tmp_path)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
