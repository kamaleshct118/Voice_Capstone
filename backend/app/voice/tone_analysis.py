from typing import Literal
from pydantic import BaseModel
from app.utils.logger import get_logger

logger = get_logger(__name__)

URGENT_KEYWORDS = [
    "emergency", "chest pain", "can't breathe", "cannot breathe",
    "bleeding", "fainted", "unconscious", "heart attack", "seizure",
    "stroke", "overdose", "poisoning", "choking", "severe", "critical",
    "dying", "collapse", "paralysis", "allergic reaction",
]

INFORMATIVE_KEYWORDS = [
    "what is", "what are", "explain", "tell me about",
    "information on", "describe", "how does", "why does",
    "define", "meaning of", "difference between", "overview of",
]


class ToneResult(BaseModel):
    tone: Literal["neutral", "alert", "informative"]
    urgency_level: int  # 0=low, 1=medium, 2=high


def analyze_tone(transcript: str) -> ToneResult:
    """Rule-based tone detection from transcript text."""
    lower = transcript.lower()

    for kw in URGENT_KEYWORDS:
        if kw in lower:
            logger.info(f"Tone: ALERT (matched: '{kw}')")
            return ToneResult(tone="alert", urgency_level=2)

    for kw in INFORMATIVE_KEYWORDS:
        if kw in lower:
            logger.info(f"Tone: INFORMATIVE (matched: '{kw}')")
            return ToneResult(tone="informative", urgency_level=0)

    logger.info("Tone: NEUTRAL")
    return ToneResult(tone="neutral", urgency_level=1)
