# app/tools/health_monitor_tool.py
# ── Health Monitoring Module ────────────────────────────────────────
# Tracks user health metrics (BP, sugar, weight, mood, symptoms).
# Persists readings to Redis DB2 AND exports them to an Excel workbook.
# Provides trend analysis and a daily checklist via one LLM call.
# ──────────────────────────────────────────────────────────────────

from typing import List, Optional
from pydantic import BaseModel
import redis
from app.cache.db0_context import append_health_log, get_health_logs
from app.llm.client import LLMClient
from app.llm.prompts import HEALTH_ANALYSIS_PROMPT
from app.llm.formatter import extract_json_from_response
from app.mcp.router import ToolOutput
from app.config import settings
from app.utils.logger import get_logger
import json
import os

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


# ── Data Model ────────────────────────────────────────────────────

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


# ── Excel Export ──────────────────────────────────────────────────

def export_to_excel(session_id: str, log_entry: dict) -> None:
    """
    Append the health log entry to an Excel workbook stored on disk.
    File path: settings.health_excel_dir / health_<session_id>.xlsx
    Creates the workbook + header row if it does not exist yet.
    """
    try:
        import openpyxl
        from datetime import datetime, timezone

        excel_dir = getattr(settings, "health_excel_dir", "health_data")
        os.makedirs(excel_dir, exist_ok=True)
        filepath = os.path.join(excel_dir, f"health_{session_id[:8]}.xlsx")

        # Column order
        headers = [
            "timestamp", "condition",
            "systolic_bp", "diastolic_bp",
            "sugar_fasting", "sugar_postmeal",
            "weight_kg", "mood", "symptoms", "notes",
        ]

        if os.path.exists(filepath):
            wb = openpyxl.load_workbook(filepath)
            ws = wb.active
        else:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Health Logs"
            ws.append(headers)

        row = [
            log_entry.get("timestamp", datetime.now(timezone.utc).isoformat()),
            log_entry.get("condition", ""),
            log_entry.get("systolic_bp", ""),
            log_entry.get("diastolic_bp", ""),
            log_entry.get("sugar_fasting", ""),
            log_entry.get("sugar_postmeal", ""),
            log_entry.get("weight_kg", ""),
            log_entry.get("mood", ""),
            ", ".join(log_entry.get("symptoms") or []),
            log_entry.get("notes", ""),
        ]
        ws.append(row)
        wb.save(filepath)
        logger.info(f"[Excel] Entry saved to {filepath}")

    except ImportError:
        logger.warning("[Excel] openpyxl not installed — skipping Excel export.")
    except Exception as e:
        logger.error(f"[Excel] Export failed: {e}")


# ── Log Entry ─────────────────────────────────────────────────────

def log_health_entry(entry: HealthLogEntry, redis_db0: redis.Redis) -> None:
    """Persist a health log entry to Redis DB2 and export to Excel."""
    from datetime import datetime, timezone
    log_dict = entry.model_dump(exclude={"session_id"})
    log_dict["timestamp"] = datetime.now(timezone.utc).isoformat()

    append_health_log(redis_db0, entry.session_id, log_dict)
    export_to_excel(entry.session_id, log_dict)


# ── Threshold Check ───────────────────────────────────────────────

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
                    break  # Only report highest level per field per reading
    return flagged


# ── Trend Analysis (with daily checklist) ────────────────────────

def analyze_health_trends(
    session_id: str,
    redis_db0: redis.Redis,
    llm_client: LLMClient,
) -> dict:
    """
    Pull health logs from DB2, run threshold checks, then make ONE LLM call
    to generate a structured health summary, recommendations, and daily checklist.
    """
    logs = get_health_logs(redis_db0, session_id, limit=30)

    if not logs:
        return {
            "summary": "No health data logged yet for this session.",
            "flagged_readings": [],
            "diet_suggestions": ["Maintain a balanced diet rich in fruits and vegetables."],
            "lifestyle_recommendations": ["Stay active with at least 30 minutes of daily exercise."],
            "mental_health_guidance": "Take time for rest and self-care.",
            "daily_checklist": [
                "Log your daily health readings",
                "Drink at least 8 glasses of water",
                "Take your prescribed medications on time",
                "Get 7-8 hours of sleep",
                "Do 30 minutes of light exercise",
            ],
            "disclaimer": _DISCLAIMER,
        }

    flagged = threshold_check(logs)
    log_summary = json.dumps(logs, indent=None)[:3000]

    user_content = (
        f"Health logs ({len(logs)} entries):\n{log_summary}\n\n"
        f"Pre-flagged readings ({len(flagged)}):\n{json.dumps(flagged)}"
    )

    messages = [
        {"role": "system", "content": HEALTH_ANALYSIS_PROMPT},
        {"role": "user", "content": user_content},
    ]

    raw = llm_client.chat(messages, max_tokens=600)
    result = extract_json_from_response(raw)

    if not result:
        result = {
            "summary": "Analysis could not be completed. Please try again.",
            "flagged_readings": flagged,
            "diet_suggestions": [],
            "lifestyle_recommendations": [],
            "mental_health_guidance": "Please consult your doctor for personalized advice.",
            "daily_checklist": [
                "Log your health readings",
                "Take medications on time",
                "Stay hydrated",
            ],
        }

    result["disclaimer"] = _DISCLAIMER
    result["flagged_readings"] = result.get("flagged_readings") or flagged

    # Ensure daily_checklist is always present
    if "daily_checklist" not in result:
        result["daily_checklist"] = [
            "Log today's health readings",
            "Take your prescribed medications",
            "Drink enough water",
            "Monitor blood pressure if applicable",
            "Get adequate rest",
        ]

    logger.info(f"[HealthMonitor] Analysis complete for session={session_id}. Flags={len(flagged)}")
    return result


# ── Health Monitoring Context (for health_monitoring intent) ──────

def get_health_context(session_id: str, redis_db0: redis.Redis) -> ToolOutput:
    """
    Return the last few health log entries as context for the LLM
    when the user asks a health-monitoring-specific question.
    """
    logs = get_health_logs(redis_db0, session_id, limit=10)
    flagged = threshold_check(logs) if logs else []

    result = {
        "recent_logs": logs[-5:] if logs else [],
        "flagged_readings": flagged,
        "total_entries": len(logs),
        "context_type": "health_monitoring",
        "success": True
    }

    return ToolOutput(
        tool_name="health_monitoring",
        result=result,
        success=True,
        confidence=0.9 if logs else 0.3,
        error=None
    )
