# app/api/health.py
# ── System Health & Debug Endpoints ─────────────────────────────
# GET /health       — liveness probe (Redis ping)
# GET /api/redis/db1 — inspect Redis DB1 (conversation cache / CAG)
# GET /api/redis/db2 — inspect Redis DB2 (context / health logs)
# ──────────────────────────────────────────────────────────────────

from datetime import datetime, timezone
from fastapi import APIRouter
from app.cache.redis_client import redis_db1, redis_db2, ping_redis

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic liveness probe — also checks Redis connectivity."""
    return {
        "status": "ok",
        "redis_db1": ping_redis(redis_db1),
        "redis_db2": ping_redis(redis_db2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/api/redis/db1")
async def inspect_redis_db1():
    """
    Debug endpoint: return all key-value pairs from Redis DB1
    (Conversation Cache / CAG — stores tool response cache).
    """
    try:
        keys = redis_db1.keys("*")
        data = {}
        for key in keys[:50]:  # Limit to 50 keys
            val = redis_db1.get(key)
            if val:
                try:
                    import json
                    data[key] = json.loads(val)
                except Exception:
                    data[key] = val
        return data
    except Exception as e:
        return {"error": str(e)}


@router.get("/api/redis/db2")
async def inspect_redis_db2():
    """
    Debug endpoint: return all key-value pairs from Redis DB2
    (Context + Health Logs — stores conversation history and health data).
    """
    try:
        keys = redis_db2.keys("*")
        data = {}
        for key in keys[:50]:  # Limit to 50 keys
            val = redis_db2.get(key)
            if val:
                try:
                    import json
                    data[key] = json.loads(val)
                except Exception:
                    data[key] = val
        return data
    except Exception as e:
        return {"error": str(e)}
