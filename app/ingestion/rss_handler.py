from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Sequence
from urllib.parse import urlparse

import feedparser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.models import Episode, RSSFeed

logger = logging.getLogger(__name__)


@dataclass
class ParsedEpisode:
    guid: str
    title: Optional[str]
    audio_url: Optional[str]
    published_at: Optional[datetime]
    summary: Optional[str]


@dataclass
class ParsedFeed:
    url: str
    title: Optional[str]
    description: Optional[str]
    episodes: List[ParsedEpisode]


async def ingest_feed(session: AsyncSession, feed_url: str) -> tuple[RSSFeed, list[Episode]]:
    """
    Ingest RSS feed and sync episodes.
    
    Args:
        session: Database session
        feed_url: URL of the RSS feed to ingest

    Returns:
        tuple of (RSSFeed instance, number of new episodes created)
    """
    parsed_feed = await fetch_feed(feed_url)
    feed = await upsert_feed(session, parsed_feed)
    new_episodes = await sync_episodes(session, feed, parsed_feed.episodes)
    # Update last_fetched via updated_at (automatic)
    return feed, new_episodes


async def fetch_feed(feed_url: str) -> ParsedFeed:
    validated_url = validate_feed_url(feed_url)
    logger.info("Fetching RSS feed: %s", validated_url)
    
    try:
        parsed = await asyncio.to_thread(feedparser.parse, validated_url)
        
        # Debug: Check what we got
        logger.info("Feed parser result: bozo=%s, version=%s, entries=%d", 
                   getattr(parsed, 'bozo', 'unknown'), 
                   getattr(parsed, 'version', 'none'), 
                   len(getattr(parsed, 'entries', [])))
        
        # Check if feed was parsed successfully
        if not hasattr(parsed, 'version') or not parsed.version:
            # Try to get more debug info
            bozo = getattr(parsed, 'bozo', False)
            if bozo:
                bozo_exception = getattr(parsed, 'bozo_exception', None)
                logger.error("Feed parsing bozo exception: %s", bozo_exception)
            raise ValueError(f"Failed to parse RSS feed: {validated_url}")

        feed_info = parsed.feed or {}
        episodes = [build_episode(entry) for entry in parsed.entries]
        logger.info("Parsed %s entries from feed %s", len(episodes), validated_url)
        return ParsedFeed(
            url=validated_url,
            title=feed_info.get("title"),
            description=feed_info.get("subtitle") or feed_info.get("description"),
            episodes=episodes,
        )
    except Exception as e:
        logger.error("Error fetching feed %s: %s", validated_url, str(e))
        raise ValueError(f"Failed to fetch or parse RSS feed: {validated_url} - {str(e)}")


async def upsert_feed(session: AsyncSession, parsed_feed: ParsedFeed) -> RSSFeed:
    result = await session.execute(select(RSSFeed).where(RSSFeed.url == parsed_feed.url))
    feed = result.scalars().first()
    if feed:
        feed.title = parsed_feed.title
        feed.description = parsed_feed.description
        return feed

    feed = RSSFeed(
        url=parsed_feed.url,
        title=parsed_feed.title,
        description=parsed_feed.description,
    )
    session.add(feed)
    await session.flush()
    return feed


async def sync_episodes(
    session: AsyncSession,
    feed: RSSFeed,
    parsed_episodes: Sequence[ParsedEpisode],
) -> List[Episode]:
    existing_guids = await fetch_existing_guids(session, feed.id)
    new_records: List[Episode] = []
    for entry in parsed_episodes:
        if entry.guid in existing_guids:
            continue
        episode = Episode(
            feed_id=feed.id,
            guid=entry.guid,
            title=entry.title,
            audio_url=entry.audio_url,
            published_at=entry.published_at,
            status="pending",
        )
        session.add(episode)
        new_records.append(episode)
    logger.info("Detected %s new episodes for feed %s", len(new_records), feed.url)
    if new_records:
        await session.flush()
    return new_records


async def fetch_existing_guids(session: AsyncSession, feed_id) -> set[str]:
    result = await session.execute(select(Episode.guid).where(Episode.feed_id == feed_id))
    return {row[0] for row in result.all()}


def build_episode(entry) -> ParsedEpisode:
    guid = entry.get("id") or entry.get("guid") or build_guid_fallback(entry)
    title = entry.get("title")
    audio_url = extract_audio_url(entry)
    published_at = parse_published(entry)
    summary = entry.get("summary") or entry.get("description")
    return ParsedEpisode(
        guid=guid,
        title=title,
        audio_url=audio_url,
        published_at=published_at,
        summary=summary,
    )


def validate_feed_url(feed_url: str) -> str:
    parsed = urlparse(feed_url)
    if not parsed.scheme.startswith("http"):
        raise ValueError("Feed URL must start with http or https")
    return feed_url


def build_guid_fallback(entry) -> str:
    source = (entry.get("title") or "") + (entry.get("link") or "")
    return hashlib.sha1(source.encode("utf-8")).hexdigest()


def extract_audio_url(entry) -> Optional[str]:
    enclosures = entry.get("enclosures") or []
    if enclosures:
        audio = next((enc for enc in enclosures if "audio" in enc.get("type", "")), enclosures[0])
        return audio.get("href")
    media_content = entry.get("media_content") or []
    if media_content:
        return media_content[0].get("url")
    links = entry.get("links") or []
    audio_link = next((link for link in links if link.get("type", "").startswith("audio")), None)
    if audio_link:
        return audio_link.get("href")
    return entry.get("link")


def parse_published(entry) -> Optional[datetime]:
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if not published:
        return None
    return datetime(*published[:6], tzinfo=timezone.utc)
