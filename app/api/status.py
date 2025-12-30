from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.storage.models import Episode, RSSFeed

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/status", tags=["status"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "rag-chatbot-api"
    }


@router.get("/queues")
async def get_queue_status() -> Dict[str, Any]:
    """Get Celery queue status."""
    try:
        from workers.celery_app import celery_app
        
        # Get active queues
        inspect = celery_app.control.inspect()
        active_queues = inspect.active_queues() or []
        
        # Get active tasks
        active_tasks = inspect.active() or {}
        
        queue_status = {}
        for queue_name in ["ingestion", "processing"]:
            queue_tasks = [task for task in active_tasks.values() 
                          if task and task.get("delivery_info", {}).get("routing_key") == queue_name]
            
            queue_status[queue_name] = {
                "active_tasks": len(queue_tasks),
                "queue_length": len([task for task in queue_tasks 
                                  if task.get("state") == "PENDING"]),
                "processing_tasks": len([task for task in queue_tasks 
                                       if task.get("state") in ["STARTED", "RETRY"]])
            }
        
        return {
            "queues": queue_status,
            "total_active_tasks": len(active_tasks),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get queue status")


@router.get("/episodes/summary")
async def get_episodes_summary(
    limit: int = Query(100, description="Limit number of episodes"),
    status_filter: Optional[str] = Query(None, description="Filter by status")
) -> Dict[str, Any]:
    """Get episodes processing summary."""
    
    with get_db() as db:
        try:
            # Base query
            query = select(Episode)
            
            # Apply status filter if provided
            if status_filter:
                query = query.where(Episode.status == status_filter)
            
            # Get counts by status
            status_counts = (
                db.execute(
                    select(Episode.status, func.count(Episode.id))
                    .group_by(Episode.status)
                )
                .all()
            )
            
            # Get total episodes
            total_episodes = db.scalar(select(func.count(Episode.id)))
            
            # Get recent episodes
            recent_episodes = (
                db.execute(
                    select(Episode)
                    .order_by(Episode.created_at.desc())
                    .limit(limit)
                )
                .all()
            )
            
            # Format status counts
            status_summary = {status: count for status, count in status_counts}
            
            return {
                "total_episodes": total_episodes,
                "status_breakdown": status_summary,
                "recent_episodes": [
                    {
                        "id": str(ep.id),
                        "title": ep.title,
                        "status": ep.status,
                        "created_at": ep.created_at.isoformat() if ep.created_at else None,
                        "processed_at": ep.processed_at.isoformat() if ep.processed_at else None,
                        "has_errors": ep.has_errors
                    }
                    for ep in recent_episodes
                ],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting episodes summary: {e}")
            raise HTTPException(status_code=500, detail="Failed to get episodes summary")


@router.get("/feeds/summary")
async def get_feeds_summary() -> Dict[str, Any]:
    """Get RSS feeds processing summary."""
    
    with get_db() as db:
        try:
            # Get all feeds with episode counts
            feeds_with_counts = (
                db.execute(
                    select(
                        RSSFeed.id,
                        RSSFeed.feed_title,
                        RSSFeed.total_episodes,
                        RSSFeed.last_fetched_at,
                        func.count(Episode.id).label("processed_episodes")
                    )
                    .outerjoin(Episode, RSSFeed.id == Episode.feed_id)
                    .group_by(RSSFeed.id)
                )
                .all()
            )
            
            feeds_summary = []
            for feed_id, title, total, last_fetched, processed in feeds_with_counts:
                feeds_summary.append({
                    "id": str(feed_id),
                    "title": title,
                    "total_episodes": total,
                    "processed_episodes": processed,
                    "completion_percentage": round((processed / total * 100) if total > 0 else 0, 2),
                    "last_fetched_at": last_fetched.isoformat() if last_fetched else None
                })
            
            return {
                "total_feeds": len(feeds_summary),
                "feeds": feeds_summary,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting feeds summary: {e}")
            raise HTTPException(status_code=500, detail="Failed to get feeds summary")
