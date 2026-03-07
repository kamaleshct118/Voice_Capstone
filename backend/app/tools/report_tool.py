# app/tools/report_tool.py
# ── Tool 3: Medical Report Generation ─────────────────────────────
# Retrieves stored user health data from Redis DB0 and uses the Health LLM
# to produce a structured summary report with personalized clinical tips.
# ──────────────────────────────────────────────────────────────────

import json
import redis
from datetime import datetime, timezone
from typing import Optional
from app.cache.db0_context import get_context, get_health_logs
from app.mcp.router import ToolOutput
from app.utils.logger import get_logger
from app.llm.health_client import HealthLLMClient

logger = get_logger(__name__)

_DISCLAIMER = (
    "This report is generated from your own logged data and is for personal "
    "awareness only. It is not medical advice or a clinical diagnosis. "
    "Always consult a qualified healthcare provider."
)

def generate_medical_report(
    session_id: str, 
    redis_db0: redis.Redis, 
    health_llm: HealthLLMClient,
    chronic_disease: Optional[str] = None
) -> ToolOutput:
    """
    Build a structured medical report for the user.
    Includes:
    - Detailed daily logs (for graphs and tables)
    - 6 AI-generated tips based on chronic condition
    - Session context summary
    """
    # 1. Pull data from Redis DB0
    conversation_history = get_context(redis_db0, session_id)
    # Get last 100 entries to ensure we have enough for a solid report/graph
    health_logs = get_health_logs(redis_db0, session_id, limit=100)

    # 2. Determine chronic disease context
    disease_context = chronic_disease or "General health monitoring"
    if not chronic_disease and health_logs:
        # Fallback to the latest log entry's chronic_disease field if not provided
        latest = health_logs[-1]
        disease_context = latest.get("chronic_disease") or latest.get("condition") or disease_context

    # 3. Generate 6 Points of Tips using Health LLM
    tips = []
    try:
        prompt = (
            f"You are Dr. Elena, a clinical health assistant. "
            f"The patient is managing the following condition: {disease_context}. "
            f"Based on this condition, provide exactly 6 specific, actionable, and compassionate health tips "
            f"to help the patient manage their condition better daily. "
            f"Return ONLY a JSON array of 6 strings. No numbers, no headers, no extra text."
        )
        raw_tips = health_llm.chat([{"role": "user", "content": prompt}], max_tokens=500)
        # Attempt to parse JSON array. LLMs sometimes add markdown backticks.
        clean_json = raw_tips.strip().replace("```json", "").replace("```", "").strip()
        tips = json.loads(clean_json)
        if not isinstance(tips, list):
            tips = [str(tips)]
    except Exception as e:
        logger.error(f"Error generating report tips: {e}")
        tips = [
            "Maintain a consistent daily schedule for monitoring.",
            "Keep a detailed record of any unusual symptoms.",
            "Stay hydrated and prioritize balanced nutrition.",
            "Ensure you are getting adequate restorative sleep.",
            "Follow your prescribed treatment plan as directed.",
            "Schedule regular follow-ups with your healthcare provider."
        ]

    # Ensure we have exactly 6 tips (trims or pads)
    tips = tips[:6]
    while len(tips) < 6:
        tips.append("Consult your doctor for personalized guidance.")

    # 4. Compile the report data
    report_data = {
        "session_id": session_id,
        "chronic_disease": disease_context,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_interactions": len(conversation_history),
        "health_tips": tips,
        "detailed_logs": health_logs,  # The full list for frontend charts/tables
        "has_health_data": bool(health_logs),
        "disclaimer": _DISCLAIMER,
    }

    logger.info(
        f"[ReportTool] Comprehensive report generated for session={session_id} | "
        f"disease={disease_context} | logs={len(health_logs)}"
    )

    return ToolOutput(
        tool_name="medical_report",
        result=report_data,
        report_data=report_data,
        success=True,
        confidence=0.98 if health_logs else 0.5,
        error=None
    )
