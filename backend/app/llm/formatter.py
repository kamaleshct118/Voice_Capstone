import re
import json
from typing import Optional


def strip_markdown(text: str) -> str:
    """Remove common markdown formatting from LLM output."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"#{1,6}\s*", "", text)
    text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate_response(text: str, max_chars: int = 500) -> str:
    """Trim to max_chars at the nearest sentence boundary."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_dot = truncated.rfind(".")
    if last_dot > max_chars // 2:
        return truncated[: last_dot + 1]
    return truncated.strip() + "..."


def extract_json_from_response(text: str) -> Optional[dict]:
    """Extract the first valid JSON object from a possibly noisy LLM response."""
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Find JSON block inside ```json ... ``` or plain {...}
    patterns = [
        r"```json\s*([\s\S]*?)```",
        r"```\s*([\s\S]*?)```",
        r"(\{[\s\S]*\})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                continue
    return None
