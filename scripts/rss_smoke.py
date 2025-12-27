import asyncio
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ingestion.rss_handler import ingest_feed  # noqa: E402
from app.storage.database import AsyncSessionLocal  # noqa: E402

TEST_FEED_URL = "https://feeds.simplecast.com/54nAGcIl"


async def main():
    async with AsyncSessionLocal() as session:
        feed, new_eps = await ingest_feed(session, TEST_FEED_URL)
        await session.commit()
        print(f"Feed: {feed.feed_title} ({feed.id})")
        print(f"Total episodes: {feed.total_episodes}, new episodes this run: {len(new_eps)}")


if __name__ == "__main__":
    asyncio.run(main())
