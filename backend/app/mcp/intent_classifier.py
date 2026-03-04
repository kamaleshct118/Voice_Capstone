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
}


class IntentResult(BaseModel):
    intent: str
    entities: dict
    raw_transcript: str


def classify_intent(transcript: str, llm_client: LLMClient) -> IntentResult:
    """Classify user intent using a lightweight LLM call."""
    messages = [
        {"role": "system", "content": INTENT_CLASSIFICATION_PROMPT},
        {"role": "user", "content": transcript},
    ]

    raw = llm_client.chat(messages, max_tokens=128, model="llama-3.1-8b-instant")
    parsed = extract_json_from_response(raw)

    if parsed and parsed.get("intent") in VALID_INTENTS:
        intent = parsed["intent"]
        entities = parsed.get("entities", {})
    else:
        # Safe fallback — general_conversation handles open-ended replies
        intent = "general_conversation"
        entities = {}
        logger.warning(f"Intent fallback to general_conversation. Raw: {raw[:80]}")

    logger.info(f"Intent: {intent} | Entities: {entities}")
    return IntentResult(intent=intent, entities=entities, raw_transcript=transcript)
