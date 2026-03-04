# app/mcp/router.py
# ── MCP — Model Control Plane ──────────────────────────────────────
# Receives classified intent and routes to the correct tool.
# Returns structured ToolOutput for the response aggregator.
# ──────────────────────────────────────────────────────────────────

from typing import List, Optional
import redis
from pydantic import BaseModel
from app.mcp.intent_classifier import IntentResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ToolOutput(BaseModel):
    tool_name: str
    result: dict
    medicine_data: Optional[dict] = None
    report_data: Optional[dict] = None
    error: Optional[str] = None


async def route_to_tools(
    intent_result: IntentResult,
    redis_db1: redis.Redis,
    redis_db0: redis.Redis,
    session_id: str,
    gemini_client=None,
) -> List[ToolOutput]:
    """
    Route the classified intent to the appropriate tool.

    Redis DB mapping
    ─────────────────────────────────────────────────────
    redis_db1 (DB1) → tool retrieval cache (CAG)
    redis_db0 (DB0) → conversation history & health logs

    Intent → Tool mapping
    ─────────────────────────────────────────────────────
    medicine_info        → medicine_classifier_tool
    medical_news         → news_tool
    medical_report       → report_tool
    health_monitoring    → health_monitor_tool (context Q&A)
    general_conversation → (no tool — LLM handles directly)
    """
    intent = intent_result.intent
    entities = intent_result.entities

    logger.info(f"[MCP] Routing intent='{intent}' session={session_id}")

    try:
        # ── Tool 1: Medicine Description & Classifier ──────────────
        if intent == "medicine_info":
            from app.tools.medicine_classifier_tool import classify_medicine
            drug_name = entities.get("drug") or intent_result.raw_transcript
            return [classify_medicine(
                input_mode="text",
                medicine_name=drug_name,
                image_bytes=None,
                redis_db1=redis_db1,
                gemini_client=gemini_client,
            )]

        # ── Tool 2: Medical & Pharmaceutical News ─────────────────
        elif intent == "medical_news":
            from app.tools.news_tool import get_medical_news
            return [get_medical_news(entities, redis_db1)]

        # ── Tool 3: Medical Report Generation ────────────────────
        elif intent == "medical_report":
            from app.tools.report_tool import generate_medical_report
            return [generate_medical_report(session_id, redis_db0)]

        # ── Health Monitoring Q&A ─────────────────────────────────
        elif intent == "health_monitoring":
            from app.tools.health_monitor_tool import get_health_context
            return [get_health_context(session_id, redis_db0)]

        # ── General Conversation — no external tool needed ────────
        elif intent == "general_conversation":
            return [ToolOutput(
                tool_name="general_conversation",
                result={"context": "general", "transcript": intent_result.raw_transcript},
            )]

        else:
            logger.warning(f"[MCP] Unrecognised intent '{intent}', falling back to general_conversation")
            return [ToolOutput(
                tool_name="general_conversation",
                result={"context": "general", "transcript": intent_result.raw_transcript},
            )]

    except Exception as e:
        logger.error(f"[MCP] Tool routing error for intent '{intent}': {e}")
        return [ToolOutput(tool_name=intent, result={}, error=str(e))]
