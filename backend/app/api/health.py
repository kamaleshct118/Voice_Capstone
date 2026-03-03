from datetime import datetime, timezone
from fastapi import APIRouter
from app.cache.redis_client import redis_db1, redis_db2, ping_redis

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "redis_db1": ping_redis(redis_db1),
        "redis_db2": ping_redis(redis_db2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
