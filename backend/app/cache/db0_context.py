import json
from datetime import datetime, timezone
from typing import List, Optional
import redis
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_CTX_PREFIX = "ctx"
_HEALTH_PREFIX = "health"


# ── Conversation Context ───────────────────────────────────────────

def get_context(client: redis.Redis, session_id: str) -> List[dict]:
    """Retrieve conversation history for a session from DB0."""
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
    """Append a message turn to session context, trimming to max_turns.
    Persists with a 7-day TTL in Redis DB0."""
    try:
        key = f"{_CTX_PREFIX}:{session_id}"
        history = get_context(client, session_id)
        history.append({"role": role, "content": content})
        if len(history) > max_turns:
            from app.llm.client import LLMClient
            llm = LLMClient(model="llama-3.3-70b-versatile")
            
            from app.llm.prompts import CONTEXT_COMPRESSION_PROMPT
            summary_prompt = CONTEXT_COMPRESSION_PROMPT
            ctx_text = "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in history)
            messages = [
                {"role": "system", "content": summary_prompt},
                {"role": "user", "content": ctx_text}
            ]
            summary = llm.chat(messages, max_tokens=150)
            
            history = [{"role": "system", "content": f"Compressed History: {summary}"}]

        client.setex(key, settings.context_ttl_seconds, json.dumps(history))
    except Exception as e:
        logger.error(f"append_context error: {e}")


def clear_context(client: redis.Redis, session_id: str) -> None:
    client.delete(f"{_CTX_PREFIX}:{session_id}")


# ── Health Logs ────────────────────────────────────────────────────

def append_health_log(client: redis.Redis, session_id: str, log_entry: dict) -> None:
    """Append a health reading to the session health log in DB0.
    Persists with a 30-day TTL."""
    try:
        key = f"{_HEALTH_PREFIX}:{session_id}"
        raw = client.get(key)
        logs: List[dict] = json.loads(raw) if raw else []
        log_entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        logs.append(log_entry)
        client.setex(key, settings.health_log_ttl_seconds, json.dumps(logs))
        logger.info(f"Health log appended for session {session_id}")
    except Exception as e:
        logger.error(f"append_health_log error: {e}")


def get_health_logs(
    client: redis.Redis, session_id: str, limit: int = 30
) -> List[dict]:
    """Retrieve the last `limit` health log entries for a session from DB0."""
    try:
        raw = client.get(f"{_HEALTH_PREFIX}:{session_id}")
        logs: List[dict] = json.loads(raw) if raw else []
        return logs[-limit:]
    except Exception as e:
        logger.error(f"get_health_logs error: {e}")
        return []


def clear_health_logs(client: redis.Redis, session_id: str) -> None:
    client.delete(f"{_HEALTH_PREFIX}:{session_id}")
