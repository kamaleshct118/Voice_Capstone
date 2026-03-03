import redis
from app.cache.db2_context import get_context
from app.mcp.router import ToolOutput
from app.utils.logger import get_logger

logger = get_logger(__name__)


def consolidate_disease_info(
    entities: dict, redis_db2: redis.Redis, session_id: str
) -> ToolOutput:
    """
    Retrieve session conversation history from DB2 and build a structured
    summary for the aggregator to process. LLM formatting happens in aggregator.
    """
    history = get_context(redis_db2, session_id)

    topics_discussed = []
    for msg in history:
        content = msg.get("content", "")
        if msg.get("role") == "user" and len(content) > 5:
            topics_discussed.append(content[:120])

    result = {
        "session_id": session_id,
        "total_turns": len(history),
        "topics_discussed": topics_discussed[:10],
        "summary_request": "Please consolidate and summarize these topics for the user.",
    }

    logger.info(f"Consolidation: {len(topics_discussed)} user turns for session {session_id}")
    return ToolOutput(tool_name="consolidation_summary", result=result)
