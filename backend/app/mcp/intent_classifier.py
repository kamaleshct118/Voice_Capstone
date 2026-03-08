from pydantic import BaseModel
from app.llm.client import LLMClient
from app.llm.prompts import INTENT_CLASSIFICATION_PROMPT
from app.llm.formatter import extract_json_from_response
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Five clean intents matching the architecture spec
VALID_INTENTS = {
    "medicine_info",        # Ask about a medicine by name or image
    "medical_news",         # Latest medical / pharmaceutical news
    "medical_report",       # Generate a summary report of the user's stored health data
    "general_conversation", # General health Q&A / chitchat
    "health_monitoring",    # Health-metric-specific queries (BP, sugar, etc.)
    "nearby_clinic",        # Find nearby clinics/hospitals
}


class IntentResult(BaseModel):
    intent: str
    entities: dict
    raw_transcript: str


def classify_intent(transcript: str, llm_client: LLMClient) -> IntentResult:
    """
    Classify user intent using lightning-fast keyword matching only.
    (Eliminated 300-400ms LLM roundtrip based on optimization #1).
    """
    transcript_lower = transcript.lower()
    
    # ── Medical Report ─────────────────────────────────────────────
    if any(kw in transcript_lower for kw in ["report", "summary", "generate", "show my data", "my history"]):
        intent = "medical_report"
        
    # ── Nearby Clinic ──────────────────────────────────────────────
    elif any(kw in transcript_lower for kw in ["find", "near", "nearby", "hospital", "clinic", "doctor", "pharmacy", "emergency", "where", "location"]):
        intent = "nearby_clinic"
        
    # ── Health Monitoring ──────────────────────────────────────────
    elif any(kw in transcript_lower for kw in ["my blood pressure", "my sugar", "my reading", "i logged", "how have i been", "my vitals", "my health"]):
        intent = "health_monitoring"
        
    # ── Medical News ───────────────────────────────────────────────
    elif any(kw in transcript_lower for kw in ["news", "latest", "recent", "update", "research", "study", "breakthrough", "clinical trial"]):
        intent = "medical_news"

    # ── Medicine Info ──────────────────────────────────────────────
    elif any(kw in transcript_lower for kw in ["what is", "tell me about", "side effects", "how to take", "dosage for"]):
        # Very rough entity extraction for medicine names since we skipped the LLM
        intent = "medicine_info"
        
    else:
        intent = "general_conversation"

    logger.info(f"Intent (0ms bypass): {intent}")
    return IntentResult(intent=intent, entities={}, raw_transcript=transcript)
