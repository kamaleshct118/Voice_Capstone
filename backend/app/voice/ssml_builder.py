# app/voice/ssml_builder.py
# ── SSML Formatting Layer ─────────────────────────────────────────
# Converts plain LLM text to safe SSML before sending to TTS.
# Tone is determined by the calling intent (medicine_info, news, report, etc.)
# The LLM NEVER writes SSML — this module does it safely.
# ──────────────────────────────────────────────────────────────────

import re
import html
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Prosody rate per tone ─────────────────────────────────────────
# alert       → slow     (emergency / important warning)
# structured  → slow     (medical report — deliberate reading pace)
# informative → medium   (medicine explanation)
# neutral     → medium   (news, general conversation)
_RATE_MAP = {
    "alert":       "slow",
    "structured":  "slow",
    "informative": "medium",
    "neutral":     "medium",
}

# ── Pitch variation per tone ──────────────────────────────────────
_PITCH_MAP = {
    "alert":       "-2st",
    "structured":  "-1st",
    "informative": "+0st",
    "neutral":     "+0st",
}


def sanitize_for_ssml(text: str) -> str:
    """Escape XML special characters for safe SSML embedding."""
    return html.escape(text, quote=False)


def build_ssml(text: str, tone: str = "neutral") -> str:
    """
    Convert plain LLM text to safe, expressive SSML.

    Tone → prosody behaviour:
      informative  →  medicine explanations         (rate=medium)
      neutral      →  news summaries, general chat  (rate=medium)
      structured   →  medical reports               (rate=slow)
      alert        →  flagged health warnings       (rate=slow, lower pitch)
    """
    safe_text = sanitize_for_ssml(text)
    rate = _RATE_MAP.get(tone, "medium")
    pitch = _PITCH_MAP.get(tone, "+0st")

    # Split on sentence boundaries and add breath pauses
    sentences = re.split(r"(?<=[.!?])\s+", safe_text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Use a longer break for structured/alert tones
    break_ms = "500ms" if tone in ("structured", "alert") else "350ms"
    body = f'\n    <break time="{break_ms}"/>'.join(sentences)

    ssml = f"""<speak>
  <prosody rate="{rate}" pitch="{pitch}">
    {body}
  </prosody>
</speak>"""

    logger.info(f"[SSML] tone={tone} rate={rate} pitch={pitch} sentences={len(sentences)}")
    return ssml
