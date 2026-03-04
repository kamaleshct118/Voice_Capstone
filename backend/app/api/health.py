# app/api/health.py
# ── System Health & Debug Endpoints ─────────────────────────────
# GET /health        — liveness probe (Redis ping)
# GET /api/redis/db0 — inspect Redis DB0 (conversation history & health logs)
# GET /api/redis/db1 — inspect Redis DB1 (tool retrieval cache / CAG)
# ──────────────────────────────────────────────────────────────────

from datetime import datetime, timezone
from fastapi import APIRouter
from app.cache.redis_client import redis_db0, redis_db1, ping_redis

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic liveness probe — also checks Redis connectivity."""
    return {
        "status": "ok",
        "redis_db0_history": ping_redis(redis_db0),
        "redis_db1_cag": ping_redis(redis_db1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/api/redis/db0")
async def inspect_redis_db0():
    """
    Debug endpoint: return all key-value pairs from Redis DB0
    (Conversation history & health logs — ctx:<session> and health:<session> keys).
    """
    try:
        keys = redis_db0.keys("*")
        data = {}
        for key in keys[:50]:  # Limit to 50 keys
            val = redis_db0.get(key)
            if val:
                try:
                    import json
                    data[key] = json.loads(val)
                except Exception:
                    data[key] = val
        return data
    except Exception as e:
        return {"error": str(e)}


@router.get("/api/redis/db1")
async def inspect_redis_db1():
    """
    Debug endpoint: return all key-value pairs from Redis DB1
    (Tool retrieval cache / CAG — stores hashed tool response chunks).
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
