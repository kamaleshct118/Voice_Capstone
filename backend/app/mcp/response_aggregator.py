# app/mcp/response_aggregator.py
# ── Response Aggregation ─────────────────────────────────────────
# Combines tool outputs + session context into ONE final LLM call.
# Selects the correct SSML tone based on intent type.
# ──────────────────────────────────────────────────────────────────

from typing import List
from app.mcp.intent_classifier import IntentResult
from app.mcp.router import ToolOutput
from app.llm.client import LLMClient
from app.llm.prompts import AGGREGATION_PROMPT, GENERAL_CONVERSATION_PROMPT
from app.llm.formatter import strip_markdown, truncate_response
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── SSML tone mapping per intent ──────────────────────────────────
# medicine_info    → informative (clear, educational delivery)
# medical_news     → neutral     (news broadcast style)
# medical_report   → structured  (deliberate, slightly slower)
# health_monitoring→ informative
# general_conv     → neutral
_TONE_MAP = {
    "medicine_info": "informative",
    "medical_news": "neutral",
    "medical_report": "structured",
    "health_monitoring": "informative",
    "general_conversation": "neutral",
}


def get_ssml_tone(intent: str) -> str:
    """Return the correct SSML tone string for the given intent."""
    return _TONE_MAP.get(intent, "neutral")


def aggregate_response(
    tool_outputs: List[ToolOutput],
    intent_result: IntentResult,
    context_history: List[dict],
    llm_client: LLMClient,
) -> str:
    """
    Combine tool outputs + session context into ONE final LLM call.
    Returns a polished, voice-ready plain-text response string.
    Filters out failed tools and prioritizes successful ones.
    """
    intent = intent_result.intent

    # ── Build tool summary block (only successful tools) ──────────
    tool_blocks = []
    successful_tools = []
    
    for output in tool_outputs:
        # Skip failed tools unless they have a user-friendly message
        if output.error and not output.result.get("message"):
            logger.warning(f"Skipping failed tool: {output.tool_name}")
            continue
            
        if output.result:
            import json
            successful_tools.append(output.tool_name)
            tool_blocks.append(f"[{output.tool_name}]: {json.dumps(output.result, indent=None)[:1500]}")

    tool_context = "\n".join(tool_blocks) or "No tool data available."
    
    if successful_tools:
        logger.info(f"Using {len(successful_tools)} successful tools: {successful_tools}")

    # ── Last 3 conversation turns for context ─────────────────────
    recent_context = context_history[-3:] if len(context_history) > 3 else context_history
    ctx_text = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}" for m in recent_context
    )

    user_content = (
        f"User query: {intent_result.raw_transcript}\n\n"
        f"Tool data:\n{tool_context}\n\n"
        f"Recent conversation:\n{ctx_text if ctx_text else 'None'}"
    )

    # ── Choose system prompt based on intent ──────────────────────
    if intent == "general_conversation":
        system_prompt = GENERAL_CONVERSATION_PROMPT
    else:
        system_prompt = AGGREGATION_PROMPT

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    raw = llm_client.chat(messages, max_tokens=300)
    cleaned = strip_markdown(raw)
    return truncate_response(cleaned, max_chars=600)

