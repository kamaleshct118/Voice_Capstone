from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Groq LLM ──────────────────────────────────────────────────
    groq_api_key: str = "placeholder"
    llm_model: str = "llama-3.1-70b-versatile"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 512
    llm_timeout: int = 30

    # ── Gemini Vision ──────────────────────────────────────────────
    gemini_api_key: str = "placeholder"
    gemini_model: str = "gemini-1.5-flash"

    # ── Redis ──────────────────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db1: int = 1
    redis_db2: int = 2
    db1_ttl_seconds: int = 86400

    # ── Whisper ────────────────────────────────────────────────────
    whisper_model_size: str = "base"
    whisper_device: str = "cpu"

    # ── Audio ──────────────────────────────────────────────────────
    max_audio_duration_sec: int = 60
    audio_sample_rate: int = 16000

    medical_api_base_url: str = "https://api.fda.gov/drug"
    news_api_key: str = "placeholder"

    # ── Server ─────────────────────────────────────────────────────
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"
    static_audio_dir: str = "static/audio"
    health_excel_dir: str = "health_data"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
