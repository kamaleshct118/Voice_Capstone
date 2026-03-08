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
    success: bool = True
    confidence: float = 1.0
    medicine_data: Optional[dict] = None
    report_data: Optional[dict] = None
    map_data: Optional[dict] = None
    error: Optional[str] = None
    cached: bool = False


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
    nearby_clinic        → nearby_clinic_tool
    general_conversation → (no tool — LLM handles directly)
    """
    intent = intent_result.intent
    entities = intent_result.entities

    logger.info(f"[MCP] Routing intent='{intent}' session={session_id}")

    try:
        import json
        import hashlib
        cache_key = None
        
        # Determine universal caching strategy
        if intent != "general_conversation":
            # Session-dependent vs Global
            scope = session_id if intent in ("medical_report", "health_monitoring") else "global"
            # Combine intent, entities, and raw query to form an absolutely unique tool cache identifier
            key_str = f"{scope}:{intent}:{json.dumps(entities, sort_keys=True)}:{intent_result.raw_transcript.lower().strip()}"
            cache_key = f"cag_tool_cache:{hashlib.md5(key_str.encode()).hexdigest()}"
            
            cached_data = redis_db1.get(cache_key)
            if cached_data:
                logger.info(f"[MCP] 🚀 REDIS DB1 CACHE HIT for {intent} (Extremely fast tool retrieval)")
                output = ToolOutput.model_validate_json(cached_data)
                output.cached = True
                return [output]

        tool_outputs = []

        # ── Tool 1: Medicine Description & Classifier ──────────────
        if intent == "medicine_info":
            from app.tools.medicine_classifier_tool import classify_medicine
            drug_name = entities.get("drug") or intent_result.raw_transcript
            tool_outputs = [classify_medicine(
                input_mode="text",
                medicine_name=drug_name,
                image_bytes=None,
                redis_db1=redis_db1,
                gemini_client=gemini_client,
            )]

        elif intent == "medical_news":
            from app.tools.news_tool import get_medical_news
            tool_outputs = [get_medical_news(entities, redis_db1)]

        # ── Tool 3: Medical Report Generation ────────────────────
        elif intent == "medical_report":
            from app.tools.report_tool import generate_medical_report
            tool_outputs = [generate_medical_report(session_id, redis_db0)]

        # ── Health Monitoring Q&A ─────────────────────────────────
        elif intent == "health_monitoring":
            from app.tools.health_monitor_tool import get_health_context
            tool_outputs = [get_health_context(session_id, redis_db0)]

        # ── Nearby Clinic Search ──────────────────────────────────
        elif intent == "nearby_clinic":
            from app.tools.nearby_clinic_tool import find_nearby_clinics
            tool_outputs = [find_nearby_clinics(entities)]

        # ── General Conversation — no external tool needed ────────
        elif intent == "general_conversation":
            return []   # Aggregator uses GENERAL_CONVERSATION_PROMPT directly

        else:
            logger.warning(f"[MCP] Unrecognised intent '{intent}', falling back to general_conversation")
            tool_outputs = [ToolOutput(
                tool_name="general_conversation",
                result={"context": "general", "transcript": intent_result.raw_transcript},
            )]

        # Store identical queries to DB1 Cache layer if execution was successful
        if cache_key and tool_outputs and tool_outputs[0].success:
            logger.info(f"[MCP] 💾 SAVING TO REDIS DB1 CACHE -> {intent} tools")
            redis_db1.setex(cache_key, 3600, tool_outputs[0].model_dump_json())

        return tool_outputs

    except Exception as e:
        logger.error(f"[MCP] Tool routing error for intent '{intent}': {e}")
        return [ToolOutput(
            tool_name=intent,
            result={"message": "Tool execution failed"},
            success=False,
            confidence=0.0,
            error=str(e)
        )]
