# app/tools/report_tool.py
# ── Tool 3: Medical Report Generation ─────────────────────────────
# Retrieves stored user health data from Redis DB2 and uses the LLM
# to produce a structured summary report shown to the user on session start.
# ──────────────────────────────────────────────────────────────────

import json
import redis
from datetime import datetime, timezone
from app.cache.db2_context import get_context, get_health_logs
from app.mcp.router import ToolOutput
from app.utils.logger import get_logger

logger = get_logger(__name__)

_DISCLAIMER = (
    "This report is generated from your own logged data and is for personal "
    "awareness only. It is not medical advice or a clinical diagnosis. "
    "Always consult a qualified healthcare provider."
)


def generate_medical_report(session_id: str, redis_db2: redis.Redis) -> ToolOutput:
    """
    Build a structured medical report for the user.

    Gathers:
    - Conversation history (what topics were discussed)
    - Health log entries (BP, sugar, weight, mood, notes)

    Returns a ToolOutput whose `report_data` field contains the structured report.
    The LLM in the response_aggregator then converts this into a voice-friendly summary.
    """
    # ── Pull data from Redis DB2 ───────────────────────────────────
    conversation_history = get_context(redis_db2, session_id)
    health_logs = get_health_logs(redis_db2, session_id, limit=50)

    # ── Summarise conversation topics ─────────────────────────────
    user_queries = [
        msg["content"][:150]
        for msg in conversation_history
        if msg.get("role") == "user"
    ][:15]

    # ── Summarise health metrics ───────────────────────────────────
    health_summary: dict = {}
    if health_logs:
        latest = health_logs[-1]
        health_summary = {
            "total_entries": len(health_logs),
            "condition": latest.get("condition", "unspecified"),
            "latest_systolic_bp": latest.get("systolic_bp"),
            "latest_diastolic_bp": latest.get("diastolic_bp"),
            "latest_fasting_sugar": latest.get("sugar_fasting"),
            "latest_postmeal_sugar": latest.get("sugar_postmeal"),
            "latest_weight_kg": latest.get("weight_kg"),
            "mood": latest.get("mood"),
            "symptoms": latest.get("symptoms") or [],
            "notes": latest.get("notes") or "",
        }

    report_data = {
        "session_id": session_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_interactions": len(conversation_history),
        "topics_discussed": user_queries,
        "health_metrics": health_summary,
        "has_health_data": bool(health_logs),
        "has_conversation_data": bool(conversation_history),
        "disclaimer": _DISCLAIMER,
    }

    logger.info(
        f"[ReportTool] Report generated for session={session_id} | "
        f"interactions={len(conversation_history)} | health_entries={len(health_logs)}"
    )

    return ToolOutput(
        tool_name="medical_report",
        result=report_data,
        report_data=report_data,
    )
