from __future__ import annotations

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.storage.models import Episode
from workers.tasks import process_episode_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/processing", tags=["processing"])


@router.post("/feeds/{feed_id}/process")
async def process_feed_episodes(
    feed_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Process all episodes in a feed."""
    
    # Get feed
    feed = await db.get(Episode, feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    # Get pending episodes
    pending_episodes = await db.execute(
        select(Episode).where(Episode.feed_id == feed_id, Episode.status == "pending")
    )
    episodes = pending_episodes.scalars().all()
    
    if not episodes:
        return {"message": "No pending episodes found", "feed_id": str(feed_id)}
    
    # Queue all episodes for processing
    task_ids = []
    for episode in episodes:
        task = process_episode_task.delay(str(episode.id))
        task_ids.append(task.id)
        logger.info(f"Queued episode {episode.id} for processing")
    
    return {
        "message": f"Queued {len(episodes)} episodes for processing",
        "feed_id": str(feed_id),
        "task_ids": task_ids,
        "episodes": [{"id": str(ep.id), "title": ep.title} for ep in episodes]
    }


@router.post("/episodes/{episode_id}/process")
async def process_single_episode(
    episode_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Process a single episode."""
    
    try:
        # Get episode
        episode = await db.get(Episode, episode_id)
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")
        
        if episode.status != "pending":
            return {
                "message": f"Episode already processed or in progress",
                "status": episode.status,
                "episode_id": str(episode_id)
            }
        
        # Queue for processing
        task = process_episode_task.delay(str(episode_id))
        
        return {
            "message": "Episode queued for processing",
            "episode_id": str(episode_id),
            "task_id": task.id,
            "status": episode.status
        }
    except Exception as e:
        logger.error(f"Error processing episode {episode_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get status of a Celery task."""
    
    try:
        from workers.celery_app import celery_app
        
        result = celery_app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
            "traceback": result.traceback if result.failed() else None
        }
    except Exception as e:
        return {
            "task_id": task_id,
            "status": "UNKNOWN",
            "error": str(e)
        }
