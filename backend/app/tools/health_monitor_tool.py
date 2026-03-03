from typing import List, Optional
from pydantic import BaseModel
import redis
from app.cache.db2_context import append_health_log, get_health_logs
from app.llm.client import LLMClient
from app.llm.prompts import HEALTH_ANALYSIS_PROMPT
from app.llm.formatter import extract_json_from_response
from app.mcp.router import ToolOutput
from app.utils.logger import get_logger
import json

logger = get_logger(__name__)

_DISCLAIMER = (
    "This is general health information only. It is not medical advice, diagnosis, or treatment. "
    "Always consult a qualified healthcare provider for any health concerns."
)

# ── Threshold definitions ──────────────────────────────────────────
THRESHOLDS = {
    "systolic_bp": [
        {"level": "danger", "min": 140},
        {"level": "warning", "min": 120},
    ],
    "diastolic_bp": [
        {"level": "danger", "min": 90},
        {"level": "warning", "min": 80},
    ],
    "sugar_fasting": [
        {"level": "danger", "min": 126},
        {"level": "warning", "min": 100},
    ],
    "sugar_postmeal": [
        {"level": "danger", "min": 200},
        {"level": "warning", "min": 140},
    ],
}


class HealthLogEntry(BaseModel):
    session_id: str
    condition: str = "other"
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    sugar_fasting: Optional[float] = None
    sugar_postmeal: Optional[float] = None
    weight_kg: Optional[float] = None
    mood: Optional[str] = None
    symptoms: Optional[List[str]] = None
    notes: Optional[str] = None


def log_health_entry(entry: HealthLogEntry, redis_db2: redis.Redis) -> None:
    """Persist a health log entry to Redis DB2."""
    append_health_log(redis_db2, entry.session_id, entry.model_dump(exclude={"session_id"}))


def threshold_check(logs: List[dict]) -> List[dict]:
    """Detect readings that exceed safe thresholds."""
    flagged = []
    for log in logs:
        ts = log.get("timestamp", "")
        for field, rules in THRESHOLDS.items():
            value = log.get(field)
            if value is None:
                continue
            for rule in rules:
                if value >= rule["min"]:
                    flagged.append({
                        "timestamp": ts,
                        "field": field,
                        "value": value,
                        "level": rule["level"],
                        "note": f"{field.replace('_', ' ').title()} = {value} exceeds {rule['level']} threshold ({rule['min']})",
                    })
                    break  # Only report the highest level per field per reading
    return flagged


def analyze_health_trends(
    session_id: str,
    redis_db2: redis.Redis,
    llm_client: LLMClient,
) -> dict:
    """
    Pull health logs from DB2, run threshold checks, then make ONE LLM call
    to generate a structured health summary with recommendations.
    """
    logs = get_health_logs(redis_db2, session_id, limit=30)

    if not logs:
        return {
            "summary": "No health data logged yet for this session.",
            "flagged_readings": [],
            "diet_suggestions": ["Maintain a balanced diet rich in fruits and vegetables."],
            "lifestyle_recommendations": ["Stay active with at least 30 minutes of daily exercise."],
            "mental_health_guidance": "Take time for rest and self-care.",
            "disclaimer": _DISCLAIMER,
        }

    flagged = threshold_check(logs)
    log_summary = json.dumps(logs, indent=None)[:3000]  # Limit token usage

    user_content = (
        f"Health logs ({len(logs)} entries):\n{log_summary}\n\n"
        f"Pre-flagged readings ({len(flagged)}):\n{json.dumps(flagged)}"
    )

    messages = [
        {"role": "system", "content": HEALTH_ANALYSIS_PROMPT},
        {"role": "user", "content": user_content},
    ]

    raw = llm_client.chat(messages, max_tokens=512)
    result = extract_json_from_response(raw)

    if not result:
        result = {
            "summary": "Analysis could not be completed. Please try again.",
            "flagged_readings": flagged,
            "diet_suggestions": [],
            "lifestyle_recommendations": [],
            "mental_health_guidance": "Please consult your doctor for personalized advice.",
        }

    result["disclaimer"] = _DISCLAIMER
    result["flagged_readings"] = result.get("flagged_readings") or flagged

    logger.info(f"Health analysis complete for session {session_id}. Flags: {len(flagged)}")
    return result
