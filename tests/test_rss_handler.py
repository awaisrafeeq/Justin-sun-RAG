from datetime import datetime

import pytest

from app.ingestion import rss_handler


def test_validate_feed_url_accepts_http():
    url = "https://example.com/feed.xml"
    assert rss_handler.validate_feed_url(url) == url


def test_validate_feed_url_rejects_non_http():
    with pytest.raises(ValueError):
        rss_handler.validate_feed_url("ftp://example.com/feed.xml")


def test_build_episode_fallback_guid_and_audio():
    entry = {
        "title": "Sample Episode",
        "link": "https://podcast.test/episodes/1",
        "media_content": [{"url": "https://cdn.test/audio.mp3"}],
    }
    episode = rss_handler.build_episode(entry)
    assert episode.title == "Sample Episode"
    assert episode.audio_url == "https://cdn.test/audio.mp3"
    assert episode.guid is not None


def test_extract_audio_url_prefers_enclosure():
    entry = {
        "enclosures": [{"href": "https://cdn.test/audio.mp3", "type": "audio/mpeg"}],
        "links": [{"href": "https://fallback.test/audio.mp3", "type": "audio/mpeg"}],
    }
    assert rss_handler.extract_audio_url(entry) == "https://cdn.test/audio.mp3"


def test_parse_published_returns_datetime():
    entry = {"published_parsed": (2024, 12, 24, 10, 30, 0, 0, 0, 0)}
    ts = rss_handler.parse_published(entry)
    assert isinstance(ts, datetime)
    assert ts.year == 2024 and ts.day == 24
