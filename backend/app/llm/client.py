from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import List
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(
        self,
        api_key: str = settings.groq_api_key,
        model: str = settings.llm_model,
        temperature: float = settings.llm_temperature,
        timeout: int = settings.llm_timeout,
    ):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=6),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def chat(self, messages: List[dict], max_tokens: int = settings.llm_max_tokens) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens,
                timeout=self.timeout,
            )
            content = response.choices[0].message.content or ""
            logger.info(f"LLM response received. Tokens: {response.usage.total_tokens}")
            return content.strip()
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise LLMError(f"LLM call failed: {e}") from e
