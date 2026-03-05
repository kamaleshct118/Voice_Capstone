from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Groq LLM ──────────────────────────────────────────────────
    groq_api_key: str = "placeholder"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 512
    llm_timeout: int = 30

    # ── Gemini Vision ──────────────────────────────────────────────
    gemini_api_key: str = "placeholder"
    gemini_model: str = "gemini-2.0-flash"

    # ── Redis ──────────────────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db0: int = 0   # DB0 — conversation history & health logs
    redis_db1: int = 1   # DB1 — tool retrieval cache (CAG)
    
    # DB0 TTL — 30 hours (108000 seconds) for conversation history & health logs
    context_ttl_seconds: int = 108000  # 30 hours for conversation context
    health_log_ttl_seconds: int = 108000  # 30 hours for health logs
    
    # DB1 TTL — 36 hours (129600 seconds) for tool retrieval cache
    ttl_drug: int = 129600     # 36 hours — OpenFDA drug info
    ttl_news: int = 129600     # 36 hours — NewsAPI articles
    ttl_medicine: int = 129600  # 36 hours — Gemini medicine classifications

    # ── Whisper ────────────────────────────────────────────────────
    whisper_model_size: str = "distil-whisper/distil-small.en"
    whisper_device: str = "cpu"

    # ── Audio ──────────────────────────────────────────────────────
    max_audio_duration_sec: int = 60
    audio_sample_rate: int = 16000

    medical_api_base_url: str = "https://api.fda.gov/drug"
    news_api_key: str = "placeholder"
    maps_api_key: str = "placeholder"
    default_location: str = "Coimbatore" # or whatever the user's city is, fallback

    # ── Server ─────────────────────────────────────────────────────
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"
    static_audio_dir: str = "static/audio"
    health_excel_dir: str = "health_data"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
