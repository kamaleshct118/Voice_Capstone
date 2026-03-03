from pydantic import BaseModel
from app.llm.client import LLMClient
from app.llm.prompts import INTENT_CLASSIFICATION_PROMPT
from app.llm.formatter import extract_json_from_response
from app.utils.logger import get_logger

logger = get_logger(__name__)

VALID_INTENTS = {
    "medical_info",
    "medical_news",
    "nearby_clinic",
    "medicine_classifier",
    "consolidation_summary",
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

    raw = llm_client.chat(messages, max_tokens=128)
    parsed = extract_json_from_response(raw)

    if parsed and parsed.get("intent") in VALID_INTENTS:
        intent = parsed["intent"]
        entities = parsed.get("entities", {})
    else:
        # Safe fallback
        intent = "medical_info"
        entities = {}
        logger.warning(f"Intent fallback to medical_info. Raw: {raw[:80]}")

    logger.info(f"Intent: {intent} | Entities: {entities}")
    return IntentResult(intent=intent, entities=entities, raw_transcript=transcript)
