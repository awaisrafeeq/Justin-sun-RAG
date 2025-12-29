import os
from pathlib import Path

import pytest

from app.ingestion.audio_processor import download_audio_to_tempfile


class _FakeResponse:
    def __init__(self, chunks):
        self._chunks = chunks

    def raise_for_status(self):
        return None

    def iter_bytes(self, chunk_size=1024):
        yield from self._chunks

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_download_audio_to_tempfile_cleans_up(monkeypatch):
    data = [b"hello", b"world"]

    def _fake_stream(*args, **kwargs):
        return _FakeResponse(data)

    import httpx

    monkeypatch.setattr(httpx, "stream", _fake_stream)

    url = "https://example.com/audio.mp3"
    with download_audio_to_tempfile(url, suffix=".mp3") as path:
        assert isinstance(path, Path)
        assert path.exists()
        assert path.read_bytes() == b"helloworld"
        tmp_path = str(path)

    assert not os.path.exists(tmp_path)
