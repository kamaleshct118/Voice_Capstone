# app/api/health.py
# -- System Health & Debug Endpoints ---------------------------------
# GET /health        -- liveness probe (Redis ping)
# GET /api/redis/db0 -- inspect Redis DB0 (conversation history)
# GET /api/redis/db1 -- inspect Redis DB1 (tool retrieval cache / CAG)
# --------------------------------------------------------------------

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter
from app.cache.redis_client import redis_db0, redis_db1, ping_redis
from app.config import settings


def _last_active_from_ttl(ttl: int, max_ttl: int) -> dict:
    """
    Derive approximate last-active time from remaining TTL.
    last_active = now - (max_ttl - ttl_remaining)
    Returns unix timestamp + human-readable string.
    """
    if ttl == -1:
        return {"last_active_ts": 0, "last_active_str": "No expiry"}
    now = datetime.now(timezone.utc)
    elapsed_seconds = max(0, max_ttl - ttl)
    last_active_dt = now - timedelta(seconds=elapsed_seconds)
    # Friendly relative string
    if elapsed_seconds < 60:
        rel = f"{elapsed_seconds}s ago"
    elif elapsed_seconds < 3600:
        rel = f"{elapsed_seconds // 60}m ago"
    elif elapsed_seconds < 86400:
        rel = f"{elapsed_seconds // 3600}h {(elapsed_seconds % 3600) // 60}m ago"
    else:
        rel = last_active_dt.strftime("%d %b %Y, %H:%M")
    return {
        "last_active_ts":  last_active_dt.timestamp(),
        "last_active_str": rel,
    }

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic liveness probe -- also checks Redis connectivity."""
    return {
        "status": "ok",
        "redis_db0_history": ping_redis(redis_db0),
        "redis_db1_cag": ping_redis(redis_db1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
