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
    client: redis.Redis, session_id: str, limit: int = 100, chronic_disease: str = None
) -> List[dict]:
    """Retrieve the health log entries for a session from DB0, optionally filtered by disease."""
    try:
        raw = client.get(f"{_HEALTH_PREFIX}:{session_id}")
        logs: List[dict] = json.loads(raw) if raw else []
        
        if chronic_disease:
            # Filter logs that match the chronic_disease OR are "General Monitoring"
            filtered = [
                l for l in logs 
                if l.get("chronic_disease", "").lower() == chronic_disease.lower() or 
                l.get("chronic_disease") in [None, "None / General Monitoring", ""]
            ]
            return filtered[-limit:]
            
        return logs[-limit:]
    except Exception as e:
        logger.error(f"get_health_logs error: {e}")
        return []


def clear_health_logs(client: redis.Redis, session_id: str) -> None:
    client.delete(f"{_HEALTH_PREFIX}:{session_id}")


def delete_health_logs_by_disease(client: redis.Redis, session_id: str, chronic_disease: str) -> None:
    """Remove all health logs associated with a specific chronic disease."""
    try:
        key = f"{_HEALTH_PREFIX}:{session_id}"
        raw = client.get(key)
        if not raw:
            return
        logs: List[dict] = json.loads(raw)
        # Filter out logs that match the chronic_disease (case-insensitive)
        filtered_logs = [
            l for l in logs 
            if l.get("chronic_disease", "").lower() != chronic_disease.lower()
        ]
        if len(filtered_logs) == len(logs):
            return
        client.setex(key, settings.health_log_ttl_seconds, json.dumps(filtered_logs))
        logger.info(f"Deleted logs for {chronic_disease} in session {session_id}")
    except Exception as e:
        logger.error(f"delete_health_logs_by_disease error: {e}")


# ── Doctor Advice Points ──────────────────────────────────────────

_ADVICE_PREFIX = "advice"

def append_doctor_advice(client: redis.Redis, session_id: str, chronic_disease: str, point: str) -> None:
    """Store a specific point or advice given by a doctor for a disease."""
    try:
        key = f"{_ADVICE_PREFIX}:{session_id}:{chronic_disease}"
        raw = client.get(key)
        points: List[dict] = json.loads(raw) if raw else []
        points.append({
            "content": point,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        # TTL matches health logs (30 days)
        client.setex(key, settings.health_log_ttl_seconds, json.dumps(points))
        logger.info(f"Doctor advice point added for {chronic_disease}")
    except Exception as e:
        logger.error(f"append_doctor_advice error: {e}")


def get_doctor_advices(client: redis.Redis, session_id: str, chronic_disease: str) -> List[dict]:
    """Retrieve all doctor advice points for a specific disease."""
    try:
        key = f"{_ADVICE_PREFIX}:{session_id}:{chronic_disease}"
        raw = client.get(key)
        return json.loads(raw) if raw else []
    except Exception as e:
        logger.error(f"get_doctor_advices error: {e}")
        return []

def delete_doctor_advices(client: redis.Redis, session_id: str, chronic_disease: str) -> None:
    client.delete(f"{_ADVICE_PREFIX}:{session_id}:{chronic_disease}")
