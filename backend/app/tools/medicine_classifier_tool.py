from typing import Optional
import redis
from app.cache.db1_cag import build_cache_key, get_cached_chunk, store_chunk
from app.llm.gemini_client import GeminiClient
from app.llm.prompts import MEDICINE_CLASSIFIER_PROMPT
from app.llm.formatter import extract_json_from_response
from app.mcp.router import ToolOutput
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_DISCLAIMER = (
    "This information is for educational purposes only. "
    "No dosage information is provided. "
    "Consult a licensed pharmacist or doctor before taking any medication."
)


def classify_medicine(
    input_mode: str,
    medicine_name: Optional[str],
    image_bytes: Optional[bytes],
    redis_db1: redis.Redis,
    gemini_client: GeminiClient,
) -> ToolOutput:
    """
    Classify a medicine using Gemini Vision (image) or Gemini text (voice/text).
    Supported modes: 'voice', 'text', 'image'
    - Does NOT use OCR — Gemini Vision natively understands images.
    - Caches results in Redis DB1 (except image mode — not reproducible by key).
    """

    # ── Cache check for voice / text modes ────────────────────────
    if input_mode in ("voice", "text") and medicine_name:
        key = build_cache_key("medicine_classifier", medicine_name)
        cached = get_cached_chunk(redis_db1, key)
        if cached:
            logger.info(f"Medicine classifier cache HIT: {medicine_name}")
            cached["input_mode"] = input_mode
            return ToolOutput(
                tool_name="medicine_classifier",
                result=cached,
                medicine_data=cached,
            )

    # ── Gemini call ───────────────────────────────────────────────
    try:
        if input_mode == "image" and image_bytes:
            raw_response = gemini_client.analyze_medicine_image(
                image_bytes, MEDICINE_CLASSIFIER_PROMPT
            )
        else:
            name = medicine_name or "unknown medicine"
            raw_response = gemini_client.classify_medicine_text(
                name, MEDICINE_CLASSIFIER_PROMPT
            )

        data = extract_json_from_response(raw_response)

        if not data:
            data = {
                "medicine_name": medicine_name or "Unknown",
                "chemical_composition": "Unable to extract",
                "drug_category": "Unknown",
                "purpose": "Unable to classify",
                "basic_safety_notes": "Consult a pharmacist.",
            }

        data["disclaimer"] = _DISCLAIMER
        data["input_mode"] = input_mode

        # ── Cache for voice/text only ──────────────────────────────
        if input_mode != "image" and medicine_name:
            key = build_cache_key("medicine_classifier", medicine_name)
            store_chunk(redis_db1, key, data, ttl=settings.cache_ttl_seconds)

        logger.info(f"Medicine classified: {data.get('medicine_name')} via {input_mode}")
        return ToolOutput(
            tool_name="medicine_classifier",
            result=data,
            medicine_data=data,
        )

    except Exception as e:
        logger.error(f"Medicine classifier error: {e}")
        fallback = {
            "medicine_name": medicine_name or "Unknown",
            "chemical_composition": "Classification failed",
            "drug_category": "Unknown",
            "purpose": "Classification failed",
            "basic_safety_notes": "Please consult a pharmacist.",
            "disclaimer": _DISCLAIMER,
            "input_mode": input_mode,
        }
        return ToolOutput(
            tool_name="medicine_classifier",
            result=fallback,
            medicine_data=fallback,
            error=str(e),
        )
