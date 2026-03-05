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
    """Classify user intent using LLM + keyword fallback for reliability."""
    
    # ── Keyword-based fallback detection (runs first for speed) ───
    transcript_lower = transcript.lower()
    
    # Medical news keywords
    news_keywords = ["news", "latest", "recent", "update", "research", "study", 
                     "discovered", "breakthrough", "pharma", "pharmaceutical", 
                     "clinical trial", "drug trial", "development"]
    
    # Nearby clinic keywords
    clinic_keywords = ["find", "near", "nearby", "hospital", "clinic", "doctor", 
                       "pharmacy", "emergency", "where", "location"]
    
    # Health monitoring keywords
    health_keywords = ["my blood pressure", "my sugar", "my reading", "i logged", 
                       "how have i been", "my vitals", "my health"]
    
    # Report keywords
    report_keywords = ["report", "summary", "generate", "show my data", "my history"]
    
    # Check for strong keyword matches
    keyword_intent = None
    if any(kw in transcript_lower for kw in news_keywords):
        keyword_intent = "medical_news"
    elif any(kw in transcript_lower for kw in clinic_keywords):
        keyword_intent = "nearby_clinic"
    elif any(kw in transcript_lower for kw in health_keywords):
        keyword_intent = "health_monitoring"
    elif any(kw in transcript_lower for kw in report_keywords):
        keyword_intent = "medical_report"
    
    # ── LLM classification ─────────────────────────────────────────
    messages = [
        {"role": "system", "content": INTENT_CLASSIFICATION_PROMPT},
        {"role": "user", "content": transcript},
    ]

    raw = llm_client.chat(messages, max_tokens=128, model="llama-3.1-8b-instant")
    parsed = extract_json_from_response(raw)

    if parsed and parsed.get("intent") in VALID_INTENTS:
        intent = parsed["intent"]
        entities = parsed.get("entities", {})
        confidence = 0.9  # High confidence when LLM returns valid intent
    else:
        # LLM failed - use keyword fallback if available
        if keyword_intent:
            intent = keyword_intent
            entities = {}
            confidence = 0.7
            logger.info(f"LLM failed, using keyword fallback: {intent}")
        else:
            intent = "general_conversation"
            entities = {}
            confidence = 0.5
            logger.warning(f"Intent fallback to general_conversation. Raw: {raw[:80]}")

    # Override LLM if keyword match is very strong and LLM disagrees
    if keyword_intent and keyword_intent != intent and confidence < 0.8:
        logger.info(f"Keyword override: {intent} → {keyword_intent}")
        intent = keyword_intent

    logger.info(f"Intent: {intent} (conf={confidence:.2f}) | Entities: {entities}")
    return IntentResult(intent=intent, entities=entities, raw_transcript=transcript)
