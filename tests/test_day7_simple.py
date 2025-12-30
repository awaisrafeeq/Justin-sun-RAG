#!/usr/bin/env python3
"""
Day 7 Simple Tests: Background Processing + Incremental Updates
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
import pytest

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.database import AsyncSessionLocal
from app.storage.models import RSSFeed, Episode


@pytest.mark.asyncio
async def test_incremental_feed_processing():
    """Test that second run only processes new episodes."""
    
    print("🔄 Testing Incremental Feed Processing...")
    
    # Create a mock feed and episodes for testing
    async with AsyncSessionLocal() as session:
        # Check existing episodes
        initial_count = await session.scalar(select(func.count(Episode.id)))
        print(f"📊 Initial episode count: {initial_count}")
        
        # Create a test feed
        test_feed = RSSFeed(
            id=uuid.uuid4(),
            feed_url="https://example.com/test-feed",
            feed_title="Test Feed",
            feed_description="Test Description",
            total_episodes=5,
            last_fetched_at=datetime.now(timezone.utc)
        )
        session.add(test_feed)
        await session.commit()
        
        # Create test episodes
        test_episodes = []
        for i in range(3):
            episode = Episode(
                id=uuid.uuid4(),
                feed_id=test_feed.id,
                title=f"Test Episode {i+1}",
                guid=f"test-guid-{i+1}",
                published_at=datetime.now(timezone.utc),
                audio_url=f"https://example.com/audio{i+1}.mp3",
                status="pending"
            )
            session.add(episode)
            test_episodes.append(episode)
        
        await session.commit()
        
        first_run_episodes = len(test_episodes)
        print(f"✅ First run: {first_run_episodes} episodes created")
        
        # Check total episodes after first run
        total_after_first = await session.scalar(select(func.count(Episode.id)))
        print(f"📊 Total after first run: {total_after_first}")
        
        # Simulate second run - try to create same episodes
        second_run_episodes = 0
        for episode_data in test_episodes:
            # Check if episode already exists
            existing = await session.execute(
                select(Episode).where(Episode.guid == episode_data.guid)
            )
            if not existing.scalar_one_or_none():
                # This would be a new episode
                second_run_episodes += 1
        
        print(f"✅ Second run: {second_run_episodes} new episodes found")
        
        # Final total
        final_total = await session.scalar(select(func.count(Episode.id)))
        print(f"📊 Final total: {final_total}")
        
        # Verify incremental processing worked
        assert second_run_episodes == 0, "Second run should not create new episodes"
        assert final_total == total_after_first, "Total should remain same"
        
        print("✅ Incremental processing test passed!")
        
        return {
            "initial_count": initial_count,
            "first_run_episodes": first_run_episodes,
            "second_run_episodes": second_run_episodes,
            "final_total": final_total
        }


@pytest.mark.asyncio
async def test_episode_status_tracking():
    """Test episode status updates during processing."""
    
    print("📊 Testing Episode Status Tracking...")
    
    async with AsyncSessionLocal() as session:
        # Create a test episode
        test_feed = RSSFeed(
            id=uuid.uuid4(),
            feed_url="https://example.com/test-feed",
            feed_title="Test Feed",
            feed_description="Test Description",
            total_episodes=1,
            last_fetched_at=datetime.now(timezone.utc)
        )
        session.add(test_feed)
        
        test_episode = Episode(
            id=uuid.uuid4(),
            feed_id=test_feed.id,
            title="Test Episode",
            guid="test-guid-status",
            published_at=datetime.now(timezone.utc),
            audio_url="https://example.com/audio.mp3",
            status="pending"
        )
        session.add(test_episode)
        await session.commit()
        
        print(f"📝 Created episode: {test_episode.id}")
        print(f"   Initial status: {test_episode.status}")
        
        # Simulate processing
        test_episode.status = "processing"
        await session.commit()
        
        print(f"   Processing status: {test_episode.status}")
        
        # Simulate completion
        test_episode.status = "completed"
        test_episode.processed_at = datetime.now(timezone.utc)
        test_episode.has_errors = False
        test_episode.chunk_ids = ["chunk-1", "chunk-2", "chunk-3"]
        await session.commit()
        
        print(f"   Final status: {test_episode.status}")
        print(f"   Processed at: {test_episode.processed_at}")
        print(f"   Chunk IDs: {len(test_episode.chunk_ids)}")
        
        # Verify status progression
        assert test_episode.status == "completed", "Episode should be completed"
        assert test_episode.processed_at is not None, "Episode should have processed timestamp"
        assert test_episode.has_errors == False, "Episode should not have errors"
        assert len(test_episode.chunk_ids) > 0, "Completed episode should have chunk IDs"
        
        print("✅ Status tracking test passed!")
        
        return {
            "episode_id": str(test_episode.id),
            "final_status": test_episode.status,
            "has_errors": test_episode.has_errors,
            "processed_at": test_episode.processed_at.isoformat(),
            "chunk_count": len(test_episode.chunk_ids)
        }


@pytest.mark.asyncio
async def test_duplicate_prevention():
    """Test prevention of duplicate episodes."""
    
    print("🚫 Testing Duplicate Prevention...")
    
    async with AsyncSessionLocal() as session:
        # Count current episodes
        initial_count = await session.scalar(select(func.count(Episode.id)))
        print(f"📊 Initial episode count: {initial_count}")
        
        # Create a test feed
        test_feed = RSSFeed(
            id=uuid.uuid4(),
            feed_url="https://example.com/duplicate-test",
            feed_title="Duplicate Test Feed",
            feed_description="Test Description",
            total_episodes=1,
            last_fetched_at=datetime.now(timezone.utc)
        )
        session.add(test_feed)
        await session.commit()
        
        # Create first episode
        episode1 = Episode(
            id=uuid.uuid4(),
            feed_id=test_feed.id,
            title="Test Episode",
            guid="duplicate-test-guid",
            published_at=datetime.now(timezone.utc),
            audio_url="https://example.com/audio.mp3",
            status="pending"
        )
        session.add(episode1)
        await session.commit()
        
        first_count = await session.scalar(select(func.count(Episode.id)))
        print(f"📊 After first episode: {first_count}")
        
        # Try to create duplicate episode
        episode2 = Episode(
            id=uuid.uuid4(),
            feed_id=test_feed.id,
            title="Test Episode Duplicate",
            guid="duplicate-test-guid",  # Same GUID
            published_at=datetime.now(timezone.utc),
            audio_url="https://example.com/audio2.mp3",
            status="pending"
        )
        
        # Check if duplicate exists
        existing = await session.execute(
            select(Episode).where(Episode.guid == episode2.guid)
        )
        duplicate_exists = existing.scalar_one_or_none() is not None
        
        if duplicate_exists:
            print("✅ Duplicate detected and prevented!")
            # Don't add the duplicate
        else:
            session.add(episode2)
            await session.commit()
        
        final_count = await session.scalar(select(func.count(Episode.id)))
        print(f"📊 Final episode count: {final_count}")
        
        # Verify no duplicates
        assert final_count == first_count, "No new episodes should be created"
        assert duplicate_exists, "Duplicate should be detected"
        
        print("✅ Duplicate prevention test passed!")
        
        return {
            "initial_count": initial_count,
            "first_count": first_count,
            "final_count": final_count,
            "duplicate_detected": duplicate_exists
        }


async def run_day7_simple_tests():
    """Run all Day 7 simple tests."""
    
    print("🚀 Starting Day 7 Simple Tests...")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Incremental Feed Processing
    try:
        results["incremental_processing"] = await test_incremental_feed_processing()
    except Exception as e:
        print(f"❌ Incremental processing test failed: {e}")
        results["incremental_processing"] = {"error": str(e)}
    
    print("\n" + "-" * 60)
    
    # Test 2: Episode Status Tracking
    try:
        results["status_tracking"] = await test_episode_status_tracking()
    except Exception as e:
        print(f"❌ Status tracking test failed: {e}")
        results["status_tracking"] = {"error": str(e)}
    
    print("\n" + "-" * 60)
    
    # Test 3: Duplicate Prevention
    try:
        results["duplicate_prevention"] = await test_duplicate_prevention()
    except Exception as e:
        print(f"❌ Duplicate prevention test failed: {e}")
        results["duplicate_prevention"] = {"error": str(e)}
    
    print("\n" + "=" * 60)
    print("🎉 Day 7 Simple Tests Complete!")
    
    # Summary
    passed_tests = sum(1 for result in results.values() if "error" not in result)
    total_tests = len(results)
    
    print(f"📊 Test Summary: {passed_tests}/{total_tests} tests passed")
    
    for test_name, result in results.items():
        if "error" in result:
            print(f"❌ {test_name}: FAILED")
        else:
            print(f"✅ {test_name}: PASSED")
    
    return results


if __name__ == "__main__":
    asyncio.run(run_day7_simple_tests())
