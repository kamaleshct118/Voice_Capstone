from typing import List, Optional
import redis
from pydantic import BaseModel
from app.mcp.intent_classifier import IntentResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ToolOutput(BaseModel):
    tool_name: str
    result: dict
    map_data: Optional[dict] = None
    medicine_data: Optional[dict] = None
    error: Optional[str] = None


async def route_to_tools(
    intent_result: IntentResult,
    redis_db1: redis.Redis,
    redis_db2: redis.Redis,
    session_id: str,
    gemini_client=None,
) -> List[ToolOutput]:
    """Route the classified intent to the appropriate tool function."""
    intent = intent_result.intent
    entities = intent_result.entities

    logger.info(f"Routing intent '{intent}' for session {session_id}")

    try:
        if intent == "medical_info":
            from app.tools.medical_api_tool import get_medical_info
            return [get_medical_info(entities, redis_db1)]

        elif intent == "medical_news":
            from app.tools.news_tool import get_medical_news
            return [get_medical_news(entities, redis_db1)]

        elif intent == "nearby_clinic":
            from app.tools.nearby_clinic_tool import find_nearby_clinics
            return [find_nearby_clinics(entities)]

        elif intent == "medicine_classifier":
            from app.tools.medicine_classifier_tool import classify_medicine
            drug_name = entities.get("drug") or intent_result.raw_transcript
            return [classify_medicine(
                input_mode="voice",
                medicine_name=drug_name,
                image_bytes=None,
                redis_db1=redis_db1,
                gemini_client=gemini_client,
            )]

        elif intent == "consolidation_summary":
            from app.tools.consolidation_tool import consolidate_disease_info
            return [consolidate_disease_info(entities, redis_db2, session_id)]

        else:
            logger.warning(f"Unknown intent '{intent}', returning empty result")
            return [ToolOutput(tool_name="unknown", result={"message": "Could not determine intent"})]

    except Exception as e:
        logger.error(f"Tool routing error for intent '{intent}': {e}")
        return [ToolOutput(tool_name=intent, result={}, error=str(e))]
