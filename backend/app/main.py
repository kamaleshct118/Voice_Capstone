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

    # 0. Detect GPU/CPU — must happen FIRST before any model is loaded
    from app.core.device import DEVICE, COMPUTE_TYPE

    # 1. Create static audio and health data directories
    os.makedirs(settings.static_audio_dir, exist_ok=True)
    os.makedirs(settings.health_excel_dir, exist_ok=True)
    logger.info(f"Static audio dir: {settings.static_audio_dir}")
    logger.info(f"Health Excel dir: {settings.health_excel_dir}")

    # 2. Load Whisper STT model
    from faster_whisper import WhisperModel
    app.state.whisper_model = WhisperModel(
        settings.whisper_model_size,
        device=DEVICE,
        compute_type=COMPUTE_TYPE,
    )
    print(
        f"\033[92m[AI] Whisper STT running on {DEVICE.upper()} "
        f"(compute={COMPUTE_TYPE})\033[0m",
        flush=True,
    )
    logger.info(f"Whisper model loaded: {settings.whisper_model_size} device={DEVICE}")

    # 3. Load Kokoro TTS engine
    from app.tts.kokoro_engine import KokoroEngine
    app.state.kokoro_engine = KokoroEngine()
    # Warmup: trigger JIT compilation so first real request is fast
    if app.state.kokoro_engine.available:
        import tempfile, os as _os
        _warmup_path = _os.path.join(settings.static_audio_dir, "_warmup.wav")
        app.state.kokoro_engine.synthesize("Ready.", _warmup_path)
        try:
            _os.remove(_warmup_path)
        except OSError:
            pass
        logger.info("Kokoro TTS warmed up successfully")

    # 4. Initialize Groq LLM client
    from app.llm.client import LLMClient
    app.state.llm_client = LLMClient(
        api_key=settings.groq_api_key,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        timeout=settings.llm_timeout,
    )
    logger.info(f"LLM client initialized: {settings.llm_model}")

    # 4.1 Initialize Dedicated Health LLM Client
    from app.llm.health_client import HealthLLMClient
    app.state.health_llm_client = HealthLLMClient(
        api_key=settings.health_llm_api_key,
        base_url=settings.health_llm_base_url,
        model=settings.health_llm_model
    )
    logger.info(f"Health LLM client initialized at: {settings.health_llm_base_url}")

    # 5. Initialize Gemini Vision client
    from app.llm.gemini_client import GeminiClient
    app.state.gemini_client = GeminiClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
    )

    # 6. Ping Redis
    from app.cache.redis_client import redis_db0, redis_db1, ping_redis
    db0_ok = ping_redis(redis_db0)
    db1_ok = ping_redis(redis_db1)
    logger.info(f"Redis DB0 (history):   {'OK' if db0_ok else 'FAILED'}")
    logger.info(f"Redis DB1 (CAG cache): {'OK' if db1_ok else 'FAILED'}")

    # 7. Initialize Postgres DB
    from app.db.postgres import init_db
    init_db()

    logger.info("Startup complete. Ready to serve requests.")
    yield

    # ── Shutdown ───────────────────────────────────────────────────
    logger.info("Shutting down...")
    from app.cache.redis_client import redis_db0, redis_db1
    redis_db0.close()
    redis_db1.close()


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
# Allow any localhost port (Vite may pick 5173, 3000, 8080, etc.)
# In production, replace the regex with your real domain.

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_origin_regex=r"http://localhost:\d+",
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
from app.api.redis_explorer import router as redis_router

app.include_router(process_router, prefix="/api", tags=["Clinical Pipeline"])
app.include_router(health_router, tags=["System Health"])
app.include_router(redis_router, prefix="/api", tags=["Redis Data Explorer"])
