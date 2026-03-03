import io
import google.generativeai as genai
from PIL import Image
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiClient:
    def __init__(
        self,
        api_key: str = settings.gemini_api_key,
        model: str = settings.gemini_model,
    ):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        logger.info(f"Gemini client initialized: {model}")

    def analyze_medicine_image(self, image_bytes: bytes, prompt: str) -> str:
        """Send an image to Gemini Vision for medicine analysis.
        Uses native vision — NOT OCR."""
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            response = self.model.generate_content([prompt, image])
            logger.info("Gemini Vision call completed (image mode)")
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini Vision error: {e}")
            raise

    def classify_medicine_text(self, medicine_name: str, prompt: str) -> str:
        """Text-only Gemini call for medicine name classification."""
        try:
            full_prompt = f"{prompt}\n\nMedicine to analyze: {medicine_name}"
            response = self.model.generate_content(full_prompt)
            logger.info(f"Gemini text classification for: {medicine_name}")
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini text error: {e}")
            raise
