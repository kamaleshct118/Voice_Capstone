import json
import hashlib
from typing import Optional
import redis
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def build_cache_key(intent: str, query: str) -> str:
    """Generate a deterministic cache key from intent + query."""
    raw = f"{intent}:{query.lower().strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get_cached_chunk(client: redis.Redis, key: str) -> Optional[dict]:
    """Retrieve a cached chunk from Redis DB1. Returns None on miss."""
    try:
        value = client.get(key)
        if value:
            logger.info(f"Cache HIT: {key[:16]}...")
            return json.loads(value)
        logger.info(f"Cache MISS: {key[:16]}...")
        return None
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None


def store_chunk(
    client: redis.Redis,
    key: str,
    data: dict,
    ttl: int = settings.db1_ttl_seconds,
) -> None:
    """Store a chunk in Redis DB1 with TTL."""
    try:
        client.setex(key, ttl, json.dumps(data))
        logger.info(f"Cached key {key[:16]}... TTL={ttl}s")
    except Exception as e:
        logger.error(f"Cache store error: {e}")
