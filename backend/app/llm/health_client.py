import json
from typing import List, Dict, Optional
from openai import OpenAI
from app.utils.logger import get_logger

logger = get_logger(__name__)

class HealthLLMClient:
    """
    Dedicated LLM client strictly for Health Monitoring using the official OpenAI client package,
    pointed to https://apidev.navigatelabsai.com/ or the specified base URL.
    """
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        # openai package usually requires the base url to end with /v1
        base_url_str = base_url.rstrip("/")
        if not base_url_str.endswith("/v1") and "v1" not in base_url_str:
            base_url_str += "/v1"
            
        self.base_url = base_url_str
        self.model = model
        
        # Initialize official OpenAI Client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=120.0
        )

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 600, temperature: float = 0.3) -> str:
        """Execute a chat completion request using the official OpenAI client."""
        logger.info(f"[HealthLLM] Sending request to {self.base_url} (model={self.model})")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content or ""
            
        except Exception as e:
            logger.error(f"[HealthLLM] Request failed: {e}")
            return '{"error": "Failed to retrieve response from Health LLM."}'
