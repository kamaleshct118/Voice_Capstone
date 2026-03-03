import json
from datetime import datetime, timezone
from typing import List, Optional
import redis
from app.utils.logger import get_logger

logger = get_logger(__name__)

_CTX_PREFIX = "ctx"
_HEALTH_PREFIX = "health"


# ── Conversation Context ───────────────────────────────────────────

def get_context(client: redis.Redis, session_id: str) -> List[dict]:
    """Retrieve conversation history for a session."""
    try:
        raw = client.get(f"{_CTX_PREFIX}:{session_id}")
        return json.loads(raw) if raw else []
    except Exception as e:
        logger.error(f"get_context error: {e}")
        return []


def append_context(
    client: redis.Redis,
    session_id: str,
    role: str,
    content: str,
    max_turns: int = 10,
) -> None:
    """Append a message turn to session context, trimming to max_turns."""
    try:
        key = f"{_CTX_PREFIX}:{session_id}"
        history = get_context(client, session_id)
        history.append({"role": role, "content": content})
        if len(history) > max_turns:
            history = history[-max_turns:]
        client.set(key, json.dumps(history))
    except Exception as e:
        logger.error(f"append_context error: {e}")


def clear_context(client: redis.Redis, session_id: str) -> None:
    client.delete(f"{_CTX_PREFIX}:{session_id}")


# ── Health Logs ────────────────────────────────────────────────────

def append_health_log(client: redis.Redis, session_id: str, log_entry: dict) -> None:
    """Append a health reading to the session health log in DB2."""
    try:
        key = f"{_HEALTH_PREFIX}:{session_id}"
        raw = client.get(key)
        logs: List[dict] = json.loads(raw) if raw else []
        log_entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        logs.append(log_entry)
        client.set(key, json.dumps(logs))
        logger.info(f"Health log appended for session {session_id}")
    except Exception as e:
        logger.error(f"append_health_log error: {e}")


def get_health_logs(
    client: redis.Redis, session_id: str, limit: int = 30
) -> List[dict]:
    """Retrieve the last `limit` health log entries for a session."""
    try:
        raw = client.get(f"{_HEALTH_PREFIX}:{session_id}")
        logs: List[dict] = json.loads(raw) if raw else []
        return logs[-limit:]
    except Exception as e:
        logger.error(f"get_health_logs error: {e}")
        return []


def clear_health_logs(client: redis.Redis, session_id: str) -> None:
    client.delete(f"{_HEALTH_PREFIX}:{session_id}")
