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


@router.get("/api/redis/db0")
async def inspect_redis_db0():
    """
    Debug endpoint: return all key-value pairs from Redis DB0
    in the structured format expected by the frontend DataPage.
    """
    import json
    try:
        keys = redis_db0.keys("*")
        entries = []

        for key in keys[:50]:
            val = redis_db0.get(key)
            ttl = redis_db0.ttl(key)        # seconds remaining, -1 = no expiry
            key_type = redis_db0.type(key)  # string, list, hash, etc.

            parsed = None
            if val:
                try:
                    parsed = json.loads(val)
                except Exception:
                    parsed = val

            # Build preview and message count for ctx: keys (list of dicts)
            preview = []
            message_count = 0
            if isinstance(parsed, list):
                message_count = len(parsed)
                preview = parsed

            ts_info = _last_active_from_ttl(ttl, settings.context_ttl_seconds)

            entries.append({
                "key":             key,
                "type":            key_type,
                "ttl_seconds":     ttl,
                "message_count":   message_count,
                "preview":         preview,
                "query_info":      None,
                "data_preview":    None,
                "last_active_ts":  ts_info["last_active_ts"],
                "last_active_str": ts_info["last_active_str"],
            })

        # Sort newest-first (highest last_active_ts first)
        entries.sort(key=lambda e: e["last_active_ts"], reverse=True)

        # Memory usage for this DB (approximate)
        try:
            info = redis_db0.info("memory")
            mem = info.get("used_memory_human", "N/A")
        except Exception:
            mem = "N/A"

        return {
            "db_name":      "DB0 - Conversation Cache",
            "total_keys":   len(keys),
            "memory_usage": mem,
            "entries":      entries,
        }
    except Exception as e:
        return {"error": str(e), "total_keys": 0, "entries": []}


@router.get("/api/redis/db1")
async def inspect_redis_db1():
    """
    Debug endpoint: return all key-value pairs from Redis DB1
    in the structured format expected by the frontend DataPage.
    """
    import json
    try:
        keys = redis_db1.keys("*")
        entries = []

        for key in keys[:50]:
            val = redis_db1.get(key)
            ttl = redis_db1.ttl(key)
            key_type = redis_db1.type(key)

            parsed = None
            if val:
                try:
                    parsed = json.loads(val)
                except Exception:
                    parsed = val

            # For DB1, extract a readable label from the cached dict
            query_info = "Cached tool response"
            if isinstance(parsed, dict):
                query_info = (
                    parsed.get("medicine_name")
                    or parsed.get("topic")
                    or parsed.get("query")
                    or "Cached tool response"
                )

            # Use ttl_news (shortest cache) as the max for DB1 entries
            max_ttl = max(settings.ttl_news, settings.ttl_medicine, settings.ttl_drug)
            ts_info = _last_active_from_ttl(ttl, max_ttl)

            entries.append({
                "key":             key,
                "type":            key_type,
                "ttl_seconds":     ttl,
                "message_count":   0,
                "preview":         [],
                "query_info":      query_info,
                "data_preview":    parsed,
                "last_active_ts":  ts_info["last_active_ts"],
                "last_active_str": ts_info["last_active_str"],
            })

        entries.sort(key=lambda e: e["last_active_ts"], reverse=True)

        try:
            info = redis_db1.info("memory")
            mem = info.get("used_memory_human", "N/A")
        except Exception:
            mem = "N/A"

        return {
            "db_name":      "DB1 - Tool Retrieval Cache",
            "total_keys":   len(keys),
            "memory_usage": mem,
            "entries":      entries,
        }
    except Exception as e:
        return {"error": str(e), "total_keys": 0, "entries": []}
