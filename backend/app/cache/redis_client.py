import redis
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# DB0 — conversation history & health logs
redis_db0: redis.Redis = redis.StrictRedis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db0,
    decode_responses=True,
)

# DB1 — tool retrieval cache (Cache-Augmented Generation)
redis_db1: redis.Redis = redis.StrictRedis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db1,
    decode_responses=True,
)


def ping_redis(client: redis.Redis) -> bool:
    try:
        return client.ping()
    except Exception as e:
        logger.error(f"Redis ping failed: {e}")
        return False
