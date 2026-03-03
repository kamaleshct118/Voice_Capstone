from typing import List
from app.mcp.intent_classifier import IntentResult
from app.mcp.router import ToolOutput
from app.llm.client import LLMClient
from app.llm.prompts import AGGREGATION_PROMPT
from app.llm.formatter import strip_markdown, truncate_response
from app.utils.logger import get_logger

logger = get_logger(__name__)


def aggregate_response(
    tool_outputs: List[ToolOutput],
    intent_result: IntentResult,
    context_history: List[dict],
    llm_client: LLMClient,
) -> str:
    """
    Combine tool outputs + session context into ONE final LLM call.
    Returns a polished, voice-ready response string.
    """
    # Build tool summary block
    tool_blocks = []
    for output in tool_outputs:
        if output.error:
            tool_blocks.append(f"[{output.tool_name}]: Error — {output.error}")
        elif output.result:
            import json
            tool_blocks.append(f"[{output.tool_name}]: {json.dumps(output.result, indent=None)}")

    tool_context = "\n".join(tool_blocks) or "No tool data available."

    # Take last 3 conversation turns for context
    recent_context = context_history[-3:] if len(context_history) > 3 else context_history
    ctx_text = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}" for m in recent_context
    )

    user_content = (
        f"User query: {intent_result.raw_transcript}\n\n"
        f"Tool data:\n{tool_context}\n\n"
        f"Recent conversation:\n{ctx_text if ctx_text else 'None'}"
    )

    messages = [
        {"role": "system", "content": AGGREGATION_PROMPT},
        {"role": "user", "content": user_content},
    ]

    raw = llm_client.chat(messages, max_tokens=256)
    cleaned = strip_markdown(raw)
    return truncate_response(cleaned, max_chars=500)
