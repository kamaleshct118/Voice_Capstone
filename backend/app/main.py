import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────
    logger.info("Starting Voice AI Healthcare Assistant v3.0")

    # 1. Create static audio and health data directories
    os.makedirs(settings.static_audio_dir, exist_ok=True)
    os.makedirs(settings.health_excel_dir, exist_ok=True)
    logger.info(f"Static audio dir: {settings.static_audio_dir}")
    logger.info(f"Health Excel dir: {settings.health_excel_dir}")

    # 2. Load Whisper STT model
    from faster_whisper import WhisperModel
    app.state.whisper_model = WhisperModel(
        settings.whisper_model_size,
        device=settings.whisper_device,
        compute_type="int8",
    )
    logger.info(f"Whisper model loaded: {settings.whisper_model_size}")

    # 3. Load Kokoro TTS engine
    from app.tts.kokoro_engine import KokoroEngine
    app.state.kokoro_engine = KokoroEngine()

    # 4. Initialize Groq LLM client
    from app.llm.client import LLMClient
    app.state.llm_client = LLMClient(
        api_key=settings.groq_api_key,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        timeout=settings.llm_timeout,
    )
    logger.info(f"LLM client initialized: {settings.llm_model}")

    # 5. Initialize Gemini Vision client
    from app.llm.gemini_client import GeminiClient
    app.state.gemini_client = GeminiClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
    )

    # 6. Ping Redis
    from app.cache.redis_client import redis_db1, redis_db2, ping_redis
    db1_ok = ping_redis(redis_db1)
    db2_ok = ping_redis(redis_db2)
    logger.info(f"Redis DB1 (CAG cache): {'OK' if db1_ok else 'FAILED'}")
    logger.info(f"Redis DB2 (context):   {'OK' if db2_ok else 'FAILED'}")

    logger.info("Startup complete. Ready to serve requests.")
    yield

    # ── Shutdown ───────────────────────────────────────────────────
    logger.info("Shutting down...")
    from app.cache.redis_client import redis_db1, redis_db2
    redis_db1.close()
    redis_db2.close()


# ── App factory ────────────────────────────────────────────────────

app = FastAPI(
    title="Voice Medical Assistant",
    description=(
        "A Multimodal Voice-Orchestrated Clinical Intelligence System with "
        "Gemini-Based Medicine Classification, Cache-Augmented Retrieval, "
        "Context Memory, and Long-Term Health Monitoring."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ───────────────────────────────────────────────────
# Create directories eagerly so StaticFiles doesn't crash on first boot.
os.makedirs(settings.static_audio_dir, exist_ok=True)
os.makedirs(settings.health_excel_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Routers ────────────────────────────────────────────────────────

from app.api.routes import router as process_router
from app.api.health import router as health_router

app.include_router(process_router, prefix="/api", tags=["Clinical Pipeline"])
app.include_router(health_router, tags=["System Health"])
