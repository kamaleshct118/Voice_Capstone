import io
from typing import Optional
import redis
from PIL import Image

from app.cache.db1_cag import build_cache_key, get_cached_chunk, store_chunk
from app.llm.gemini_client import GeminiClient
from app.mcp.router import ToolOutput
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_DISCLAIMER = (
    "This information is for educational purposes only. "
    "Amounts and administration instructions are not provided. "
    "Consult a licensed pharmacist or doctor before taking any medication."
)

def extract_text(image_bytes: bytes, model) -> Optional[str]:
    try:
        logger.info("Extracting text from image")
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image = image.resize((1024, 1024))
        prompt = """You are performing OCR on a pharmaceutical package.
Extract ALL visible text exactly as written on the package.
Return ONLY the extracted text.
Do not summarize."""
        response = model.generate_content([prompt, image])
        
        text = ""
        if hasattr(response, "text") and getattr(response, "text", ""):
            text = response.text
        else:
            try:
                text = response.candidates[0].content.parts[0].text
            except Exception:
                pass
        text = text.strip()
        if not text:
            logger.info("No text detected")
            return None
        logger.info("Text extraction completed")
        return text
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return None

def detect_medicine(text: str, model) -> Optional[str]:
    try:
        logger.info("Detecting medicine from text")
        prompt = f"""You are analyzing pharmaceutical packaging text.
Text:
{text}
Identify if a MEDICINE name or ACTIVE INGREDIENT exists.
Return result in this format:
Medicine:
Generic:
If no medicine name is present return:
NO_MEDICINE_DETECTED"""
        response = model.generate_content(prompt)
        result = response.text.strip()
        if "NO_MEDICINE_DETECTED" in result:
            logger.info("No medicine detected")
            return None
        logger.info("Medicine identified")
        return result
    except Exception as e:
        logger.error(f"Medicine detection failed: {e}")
        return None

def medicine_template(medicine_info: str, model) -> str:
    try:
        logger.info("Generating medicine explanation")
        prompt = f"""Medicine information:
{medicine_info}

Explain this medicine clearly in a natural, spoken tone.
Do NOT include the "Medicine:" or "Generic:" headers. Just start explaining what the medication is.
Cover the following:
- What it is and its category
- What it is used for
- Common side effects
- A brief medical warning

Format the response strictly with plain text. Make lists use plain dashes. 
Always end EVERY bullet point and sentence with a full stop (.).
Do not use asterisks or markdown bolding. Limit response to 100 words."""
        response = model.generate_content(prompt)
        text = response.text.replace("*", "").strip()
        return text
    except Exception as e:
        logger.error(f"Template generation failed: {e}")
        return "Sorry, medicine explanation could not be generated."

def answer_with_context(medicine_info: str, question: str, model) -> str:
    try:
        logger.info("Processing contextual question")
        prompt = f"""Medicine information:
{medicine_info}

User question:
{question}

Answer the user's question clearly and briefly in a natural, spoken tone.
Always end EVERY bullet point and sentence with a full stop (.).
Structure your response exactly like this (use plain text dashes, NO bolding, NO asterisks, NO markdown):
Answer: [Direct answer to the user's question].
Used For:
- [point].
- [point].
Common Side Effects:
- [point].
- [point].
Medical Warning: [Brief safety note].

Strictly limit to 100 words."""
        response = model.generate_content(prompt)
        text = response.text.replace("*", "").strip()
        return text
    except Exception as e:
        logger.error(f"Context answer failed: {e}")
        return "Sorry, I could not answer the question."

def text_query(question: str, model) -> str:
    try:
        logger.info("Text query mode")
        prompt = f"""Answer the following medicine question briefly in a natural, spoken tone.
Question:
{question}

Structure your response exactly like this (use plain text dashes, NO bolding, NO asterisks, NO markdown):
Explanation: [Explain what the medicine is].
Used For:
- [point].
- [point].
Common Side Effects:
- [point].
- [point].
Medical Warning: [Brief physician consultation warning].

Always end EVERY bullet point and sentence with a full stop (.).
Strictly limit response to 100 words."""
        response = model.generate_content(prompt)
        text = response.text.replace("*", "").strip()
        return text
    except Exception as e:
        logger.error(f"Text query error: {e}")
        return "Sorry, I could not process the question."

def parse_medicine_info(text: str):
    med_name = "Unknown"
    generic = "Unknown"
    for line in text.split('\n'):
        if line.startswith("Medicine:"):
            med_name = line.replace("Medicine:", "").strip()
        if line.startswith("Generic:"):
            generic = line.replace("Generic:", "").strip()
    return med_name, generic

def classify_medicine(
    input_mode: str,
    medicine_name: Optional[str],
    image_bytes: Optional[bytes],
    redis_db1: redis.Redis,
    gemini_client: GeminiClient,
) -> ToolOutput:
    """Classify a medicine using Gemini Vision. IPYNB Modalities supported."""
    if input_mode in ("voice", "text") and medicine_name:
        key = build_cache_key("medicine_info", medicine_name)
        cached = get_cached_chunk(redis_db1, key)
        if cached:
            logger.info(f"Medicine classifier cache HIT: {medicine_name}")
            cached["input_mode"] = input_mode
            return ToolOutput(tool_name="medicine_info", result=cached, medicine_data=cached)

    model = gemini_client.model
    data = {"medicine_name": "Unknown", "chemical_composition": "Unknown", "drug_category": "Unknown", "purpose": "Processing failed.", "basic_safety_notes": "Please consult a pharmacist.", "disclaimer": _DISCLAIMER, "input_mode": input_mode}
    success = False

    try:
        if image_bytes and medicine_name and input_mode == "image+text":
            logger.info("Mode: image + text")
            text = extract_text(image_bytes, model)
            if not text:
                data["purpose"] = "Sorry, text could not be extracted from the image."
            else:
                medicine = detect_medicine(text, model)
                if not medicine:
                    data["purpose"] = "Sorry, I could not identify a medicine name in the label."
                else:
                    med_name, generic = parse_medicine_info(medicine)
                    data["medicine_name"] = med_name
                    data["chemical_composition"] = generic
                    data["purpose"] = answer_with_context(medicine, medicine_name, model)
                    success = True

        elif image_bytes and input_mode == "image":
            logger.info("Mode: image only")
            text = extract_text(image_bytes, model)
            if not text:
                data["purpose"] = "Sorry, text could not be extracted from the image."
            else:
                medicine = detect_medicine(text, model)
                if not medicine:
                    data["purpose"] = "Sorry, the image does not appear to contain a recognizable medicine."
                else:
                    med_name, generic = parse_medicine_info(medicine)
                    data["medicine_name"] = med_name
                    data["chemical_composition"] = generic
                    data["purpose"] = medicine_template(medicine, model)
                    success = True

        elif medicine_name:
            logger.info("Mode: text/voice only")
            data["medicine_name"] = medicine_name.capitalize()
            # If the user asks a clarification, the answer describes exactly the medicine.
            data["purpose"] = text_query(medicine_name, model)
            success = True
        else:
            logger.info("No valid input.")
            data["purpose"] = "Please provide an image or question."

        if success and input_mode in ("voice", "text") and medicine_name and data["purpose"] and "Sorry" not in data["purpose"]:
            key = build_cache_key("medicine_info", medicine_name)
            store_chunk(redis_db1, key, data, ttl=settings.ttl_medicine)

        return ToolOutput(
            tool_name="medicine_info",
            result=data,
            medicine_data=data,
            success=success,
            confidence=0.85 if data.get("medicine_name") != "Unknown" else 0.3,
            error=None
        )

    except Exception as e:
        logger.error(f"Medicine classifier error: {e}")
        fallback = {"medicine_name": medicine_name or "Unknown", "chemical_composition": "Classification failed", "drug_category": "Unknown", "purpose": "Classification failed", "basic_safety_notes": "Please consult a pharmacist.", "disclaimer": _DISCLAIMER, "input_mode": input_mode}
        return ToolOutput(tool_name="medicine_info", result=fallback, medicine_data=fallback, success=False, confidence=0.0, error=str(e))
