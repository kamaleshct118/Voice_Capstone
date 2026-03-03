import html
from app.utils.logger import get_logger

logger = get_logger(__name__)

_RATE_MAP = {
    "alert": "slow",
    "informative": "medium",
    "neutral": "medium",
}


def sanitize_for_ssml(text: str) -> str:
    """Escape XML special characters for safe SSML embedding."""
    return html.escape(text, quote=False)


def build_ssml(text: str, tone: str = "neutral") -> str:
    """
    Convert plain LLM text to safe, expressive SSML.
    - Splits on sentence boundaries and adds breaks.
    - Adjusts prosody rate based on tone.
    - LLM NEVER writes SSML — this module does it safely.
    """
    safe_text = sanitize_for_ssml(text)
    rate = _RATE_MAP.get(tone, "medium")

    # Split into sentences
    import re
    sentences = re.split(r"(?<=[.!?])\s+", safe_text)
    sentences = [s.strip() for s in sentences if s.strip()]

    body = '\n    <break time="350ms"/>'.join(sentences)

    ssml = f"""<speak>
  <prosody rate="{rate}">
    {body}
  </prosody>
</speak>"""

    logger.info(f"SSML built: tone={tone} rate={rate} sentences={len(sentences)}")
    return ssml
