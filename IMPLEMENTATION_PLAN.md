# Multimodal Voice-Orchestrated Clinical Intelligence System
## Full Implementation Plan (Updated)

> **System Title:**
> *A Multimodal Voice-Orchestrated Clinical Intelligence System with Gemini-Based Medicine Classification,
> Cache-Augmented Retrieval, Context Memory, and Long-Term Health Monitoring.*

---

## What Changed From Previous Plan

| Area | Change |
|------|--------|
| `medicine_availability_tool.py` | **REMOVED** entirely |
| `medicine_classifier` tool | **ADDED** — voice + text + image (Gemini Vision) |
| `health_monitor_analysis` tool | **ADDED** — long-term condition tracking via Redis DB2 |
| `/health-monitor` frontend page | **ADDED** — dedicated health monitoring UI |
| `types/clinical.ts` | **UPDATED** — new tool types + response shapes |
| `App.tsx` | **UPDATED** — new `/health-monitor` route |
| Backend tool layer | **6 final tools** (see below) |

---

## Final Tool Layer

```
medical_info           → OpenFDA medical knowledge (CAG cached, DB1)
medical_news           → NewsAPI medical headlines (CAG cached, DB1)
nearby_clinic          → Google Maps clinic locator (map_data returned)
medicine_classifier    → Gemini Vision image/text/voice classification (CAG cached, DB1)
health_monitor_analysis → Threshold-based trend analysis (context from DB2)
consolidation_summary  → Session overview from DB2 history
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Vite + React)                  │
│                                                                 │
│  /               → LandingPage.tsx                              │
│  /assistant      → AssistantPage.tsx  (voice + text + image)    │
│  /data           → DataPage.tsx                                 │
│  /health-monitor → HealthMonitorPage.tsx  (NEW)                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │  HTTP (multipart/form-data or JSON)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                          │
│                                                                 │
│  POST /api/process          → main voice/text pipeline          │
│  POST /api/classify-medicine → medicine_classifier endpoint     │
│  POST /api/health-log       → log health parameters             │
│  GET  /api/health-summary   → retrieve trend analysis           │
│  GET  /health               → health check                      │
└────────────┬────────────────────────────┬───────────────────────┘
             │                            │
    ┌────────▼────────┐          ┌────────▼────────┐
    │  Redis DB1      │          │  Redis DB2      │
    │  CAG Cache      │          │  Session Context│
    │  (TTL enabled)  │          │  + Health Logs  │
    └─────────────────┘          └─────────────────┘
```

---

## Updated Backend File Structure

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   │
│   ├── api/
│   │   ├── routes.py           ← main pipeline + medicine classifier endpoint
│   │   └── health.py           ← /health status check
│   │
│   ├── voice/
│   │   ├── vad.py
│   │   ├── stt.py
│   │   ├── tone_analysis.py
│   │   └── ssml_builder.py
│   │
│   ├── mcp/
│   │   ├── intent_classifier.py
│   │   ├── router.py
│   │   └── response_aggregator.py
│   │
│   ├── tools/
│   │   ├── medical_api_tool.py
│   │   ├── news_tool.py
│   │   ├── nearby_clinic_tool.py
│   │   ├── medicine_classifier_tool.py  ← NEW (replaces medicine_availability)
│   │   ├── health_monitor_tool.py       ← NEW
│   │   └── consolidation_tool.py
│   │
│   ├── cache/
│   │   ├── redis_client.py
│   │   ├── db1_cag.py
│   │   └── db2_context.py              ← extended for health logs
│   │
│   ├── llm/
│   │   ├── client.py                   ← Groq client
│   │   ├── gemini_client.py            ← NEW — Gemini Vision client
│   │   ├── prompts.py
│   │   └── formatter.py
│   │
│   ├── tts/
│   │   └── kokoro_engine.py
│   │
│   └── utils/
│       ├── logger.py
│       ├── metrics.py
│       └── validators.py
│
├── docker/
│   ├── docker-compose.yml
│   └── redis.conf
│
├── tests/
│   ├── test_cache.py
│   ├── test_mcp.py
│   ├── test_tools.py
│   └── test_medicine_classifier.py     ← NEW
│
├── .env
├── requirements.txt
└── run.py
```

---

## Updated Frontend File Structure

```
frontend/src/
├── App.tsx                               ← ADD /health-monitor route
├── pages/
│   ├── LandingPage.tsx                   ← no change
│   ├── AssistantPage.tsx                 ← ADD image upload support
│   ├── DataPage.tsx                      ← no change
│   ├── HealthMonitorPage.tsx             ← NEW
│   └── NotFound.tsx                      ← no change
│
├── components/
│   ├── ChatInput.tsx                     ← ADD image upload button
│   ├── ResponseCard.tsx                  ← ADD medicine_classifier + health_monitor cards
│   ├── MedicineClassifierCard.tsx        ← NEW
│   ├── HealthLogForm.tsx                 ← NEW
│   ├── HealthTrendChart.tsx              ← NEW
│   ├── HealthSummaryCard.tsx             ← NEW
│   ├── AudioPlayer.tsx                   ← no change
│   ├── ChatSidebar.tsx                   ← no change
│   ├── MapPopup.tsx                      ← no change
│   └── NavLink.tsx                       ← no change
│
├── hooks/
│   ├── useVoiceRecorder.ts               ← extract from ChatInput (optional refactor)
│   └── useHealthMonitor.ts               ← NEW
│
└── types/
    └── clinical.ts                       ← UPDATED (new types)
```

---

## Implementation Phases

---

### Phase 0 — Project Root Files

---

#### `.env` (UPDATED)
```ini
# LLM — Groq
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=llama-3.1-70b-versatile
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=512
LLM_TIMEOUT=30

# Gemini Vision
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB1=1
REDIS_DB2=2
DB1_TTL_SECONDS=86400

# Whisper
WHISPER_MODEL_SIZE=base
WHISPER_DEVICE=cpu

# Audio
MAX_AUDIO_DURATION_SEC=60
AUDIO_SAMPLE_RATE=16000

# External APIs
MEDICAL_API_BASE_URL=https://api.fda.gov/drug
NEWS_API_KEY=your_newsapi_key_here
MAPS_API_KEY=your_google_maps_key_here

# Server
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
STATIC_AUDIO_DIR=static/audio
```

---

#### `requirements.txt` (UPDATED)
```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
python-multipart
pydantic>=2.0
pydantic-settings

# Redis
redis>=5.0.0

# STT
faster-whisper>=1.0.0

# Audio
librosa>=0.10.0
soundfile>=0.12.0
numpy>=1.24.0

# LLM — Groq
groq>=0.5.0
httpx>=0.27.0
tenacity>=8.2.0

# LLM — Gemini Vision
google-generativeai>=0.7.0

# TTS
kokoro>=0.9.0

# Utils
python-dotenv
aiofiles
pillow>=10.0.0
```

---

#### `run.py`
```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

---

### Phase 1 — Config & Infrastructure

---

#### `app/config.py` (UPDATED)

```python
class Settings(BaseSettings):
    # Groq
    groq_api_key: str
    llm_model: str = "llama-3.1-70b-versatile"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 512
    llm_timeout: int = 30

    # Gemini
    gemini_api_key: str
    gemini_model: str = "gemini-1.5-flash"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db1: int = 1
    redis_db2: int = 2
    db1_ttl_seconds: int = 86400

    # Whisper
    whisper_model_size: str = "base"
    whisper_device: str = "cpu"

    # Audio
    max_audio_duration_sec: int = 60
    audio_sample_rate: int = 16000

    # APIs
    medical_api_base_url: str
    news_api_key: str
    maps_api_key: str

    # Server
    allowed_origins: str = "http://localhost:5173"
    static_audio_dir: str = "static/audio"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

---

#### `app/dependencies.py`
```python
# Singleton dependency injection
def get_redis_db1() -> redis.Redis
def get_redis_db2() -> redis.Redis
def get_llm_client() -> LLMClient
def get_gemini_client() -> GeminiClient   ← NEW
def get_whisper_model() -> WhisperModel
def get_kokoro_engine() -> KokoroEngine
```

---

#### `app/main.py`
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load all models once
    app.state.whisper_model = load_whisper_model()
    app.state.kokoro_engine = load_kokoro_engine()
    app.state.llm_client = LLMClient(...)
    app.state.gemini_client = GeminiClient(...)    ← NEW
    app.state.redis_db1 = get_redis_db1()
    app.state.redis_db2 = get_redis_db2()
    os.makedirs(settings.static_audio_dir, exist_ok=True)
    yield
    # Shutdown: close connections

# Routers registered:
# POST /api/process
# POST /api/classify-medicine          ← NEW
# POST /api/health-log                 ← NEW
# GET  /api/health-summary/{session_id} ← NEW
# GET  /health
```

---

### Phase 2 — Cache Layer

---

#### `app/cache/redis_client.py`
```python
redis_db1 = StrictRedis(db=1, decode_responses=True)
redis_db2 = StrictRedis(db=2, decode_responses=True)

def ping_redis(client) -> bool
```

---

#### `app/cache/db1_cag.py`
CAG for medical knowledge + medicine classification results.

```python
def build_cache_key(intent: str, query: str) -> str
    # sha256(f"{intent}:{query.lower().strip()}")

def get_cached_chunk(client, key) -> Optional[dict]
def store_chunk(client, key, data: dict, ttl: int) -> None
```

---

#### `app/cache/db2_context.py` (EXTENDED)
Now handles both conversation history AND health logs.

```python
# ── Conversation context ──────────────────────────────────────────
def get_context(client, session_id) -> List[dict]
def append_context(client, session_id, role, content, max_turns=10) -> None
def clear_context(client, session_id) -> None

# ── Health log storage (NEW) ──────────────────────────────────────
def append_health_log(client, session_id, log_entry: dict) -> None
    # Key: health:{session_id}  → JSON list of log entries
    # Each log: {timestamp, condition, bp, sugar, weight, mood, symptoms, ...}

def get_health_logs(client, session_id, limit=30) -> List[dict]
    # Returns last `limit` log entries, sorted by timestamp

def clear_health_logs(client, session_id) -> None
```

---

### Phase 3 — LLM Layer

---

#### `app/llm/client.py` — Groq
```python
class LLMClient:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential())
    def chat(self, messages: List[dict], max_tokens: int = 512) -> str
```

---

#### `app/llm/gemini_client.py` — NEW
Dedicated Gemini Vision client.

```python
import google.generativeai as genai
from PIL import Image
import io

class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def analyze_medicine_image(self, image_bytes: bytes, prompt: str) -> str:
        # Convert bytes → PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        # Send to Gemini Vision with structured prompt
        response = self.model.generate_content([prompt, image])
        return response.text

    def classify_medicine_text(self, medicine_name: str, prompt: str) -> str:
        # Text-only Gemini call for name/transcript-based classification
        response = self.model.generate_content(f"{prompt}\nMedicine: {medicine_name}")
        return response.text
```

---

#### `app/llm/prompts.py` (UPDATED)

```python
INTENT_CLASSIFICATION_PROMPT = """
Classify the user query into one of:
medical_info | medical_news | nearby_clinic | medicine_classifier | consolidation_summary

Return JSON: {"intent": "...", "entities": {"disease": ..., "drug": ..., "location": ...}}
Never diagnose. If unclear, default to medical_info.
"""

AGGREGATION_PROMPT = """
You are a clinical voice assistant. Summarize the tool result clearly and concisely.
Under 3 short sentences. Never suggest dosage. Always recommend seeing a doctor.
"""

CONSOLIDATION_PROMPT = """
Based on conversation history, give a brief overview of the topics discussed.
No diagnosis. Recommend professional consultation.
"""

MEDICINE_CLASSIFIER_PROMPT = """
You are analyzing a medicine. Extract and return ONLY valid JSON:
{
  "medicine_name": "...",
  "chemical_composition": "...",
  "drug_category": "...",
  "purpose": "...",
  "basic_safety_notes": "..."
}
Do not suggest dosage. Do not recommend the medicine. Be factual and non-prescriptive.
"""

HEALTH_ANALYSIS_PROMPT = """
You are a health trend analyst (not a doctor). Analyze the logged health data.
Identify patterns and flag any values outside safe thresholds.
Return:
{
  "summary": "...",
  "flagged_readings": [...],
  "diet_suggestions": [...],
  "lifestyle_recommendations": [...],
  "mental_health_guidance": "...",
  "disclaimer": "This is not medical advice. Consult a healthcare provider."
}
"""
```

---

#### `app/llm/formatter.py`
```python
def strip_markdown(text: str) -> str
def truncate_response(text: str, max_chars: int = 500) -> str
def extract_json_from_response(text: str) -> dict
```

---

### Phase 4 — Voice Pipeline

---

#### `app/voice/vad.py`
```python
# Silence trimming with librosa.effects.trim()
# Duration validation (min 0.5s, max MAX_AUDIO_DURATION_SEC)
def process_audio(audio_bytes: bytes, sample_rate: int) -> np.ndarray
```

---

#### `app/voice/stt.py`
```python
class STTResult(BaseModel):
    transcript: str
    confidence: float
    language: str

def transcribe(audio_array: np.ndarray, model: WhisperModel) -> STTResult
```

---

#### `app/voice/tone_analysis.py`
Rule-based, no external model.

```python
URGENT_KEYWORDS = ["emergency", "chest pain", "can't breathe", "bleeding", ...]
INFORMATIVE_KEYWORDS = ["what is", "explain", "tell me about", ...]

class ToneResult(BaseModel):
    tone: Literal["neutral", "alert", "informative"]
    urgency_level: int  # 0=low, 1=medium, 2=high

def analyze_tone(transcript: str) -> ToneResult
```

---

#### `app/voice/ssml_builder.py`
LLM never generates SSML. This module does it safely.

```python
def sanitize_for_ssml(text: str) -> str
    # Escape &, <, >

def build_ssml(text: str, tone: str = "neutral") -> str
    # → <speak><prosody rate="...">sentences<break time="400ms"/>...</prosody></speak>
```

---

### Phase 5 — MCP Layer

---

#### `app/mcp/intent_classifier.py` (UPDATED)

```python
VALID_INTENTS = [
    "medical_info",
    "medical_news",
    "nearby_clinic",
    "medicine_classifier",    ← replaces medicine_availability
    "consolidation_summary"
]

class IntentResult(BaseModel):
    intent: str
    entities: dict
    raw_transcript: str

def classify_intent(transcript: str, llm_client: LLMClient) -> IntentResult
```

> Note: `health_monitor_analysis` is NOT classified via MCP — it has its own dedicated route.

---

#### `app/mcp/router.py` (UPDATED)

| Intent | Tool |
|--------|------|
| `medical_info` | `medical_api_tool.get_medical_info()` |
| `medical_news` | `news_tool.get_medical_news()` |
| `nearby_clinic` | `nearby_clinic_tool.find_nearby_clinics()` |
| `medicine_classifier` | `medicine_classifier_tool.classify_medicine()` |
| `consolidation_summary` | `consolidation_tool.consolidate_disease_info()` |

```python
class ToolOutput(BaseModel):
    tool_name: str
    result: dict
    map_data: Optional[dict] = None
    medicine_data: Optional[dict] = None   ← NEW field
    error: Optional[str] = None

async def route_to_tools(intent_result, redis_db1, redis_db2, session_id) -> List[ToolOutput]
```

---

#### `app/mcp/response_aggregator.py`
```python
def aggregate_response(
    tool_outputs: List[ToolOutput],
    intent_result: IntentResult,
    context_history: List[dict],
    llm_client: LLMClient
) -> str
# ONE final LLM call using AGGREGATION_PROMPT
```

---

### Phase 6 — Tools

---

#### `app/tools/medical_api_tool.py`
```python
def get_medical_info(entities: dict, redis_db1: Redis) -> ToolOutput:
    # 1. build_cache_key("medical_info", entities["disease"])
    # 2. Cache HIT → return directly (no API call)
    # 3. Cache MISS → GET https://api.fda.gov/drug/label.json?search=...
    # 4. Extract: indications, warnings, description
    # 5. store_chunk() with TTL
    # 6. Return ToolOutput
```

---

#### `app/tools/news_tool.py`
```python
def get_medical_news(entities: dict, redis_db1: Redis) -> ToolOutput:
    # Cache TTL = 3600s (news must be fresh)
    # NewsAPI: /v2/everything?q={topic}&language=en&pageSize=3
    # Return top 3: title, description, url, publishedAt
```

---

#### `app/tools/nearby_clinic_tool.py`
```python
def find_nearby_clinics(entities: dict) -> ToolOutput:
    # Geocode location → lat/lng
    # Google Maps Places API: nearbysearch, type=hospital, radius=5000
    # Return top 5: name, address, lat, lng, phone
    # map_data = {"type": "clinics", "locations": [...]}
```

---

#### `app/tools/medicine_classifier_tool.py` — NEW

This is the core new tool. Handles 3 input modes:

```python
class MedicineClassifierResult(BaseModel):
    medicine_name: str
    chemical_composition: str
    drug_category: str
    purpose: str
    basic_safety_notes: str
    input_mode: Literal["voice", "text", "image"]
    disclaimer: str = "This information is educational only. Consult a pharmacist or doctor."

def classify_medicine(
    input_mode: str,           # "voice" | "text" | "image"
    medicine_name: str,        # for voice/text modes
    image_bytes: bytes,        # for image mode (None if not image)
    redis_db1: Redis,
    gemini_client: GeminiClient
) -> ToolOutput:

    # ── Cache check (for voice + text modes) ─────────────────────
    if input_mode in ("voice", "text") and medicine_name:
        key = build_cache_key("medicine_classifier", medicine_name)
        cached = get_cached_chunk(redis_db1, key)
        if cached:
            return ToolOutput(tool_name="medicine_classifier",
                              result=cached, medicine_data=cached)

    # ── Gemini call ───────────────────────────────────────────────
    if input_mode == "image":
        raw = gemini_client.analyze_medicine_image(image_bytes, MEDICINE_CLASSIFIER_PROMPT)
    else:
        raw = gemini_client.classify_medicine_text(medicine_name, MEDICINE_CLASSIFIER_PROMPT)

    # ── Parse structured JSON from Gemini response ─────────────────
    data = extract_json_from_response(raw)
    data["input_mode"] = input_mode
    data["disclaimer"] = "Educational only. Consult a pharmacist."

    # ── Cache result (skip for image — not reproducible by key) ───
    if input_mode != "image":
        store_chunk(redis_db1, key, data, ttl=86400)

    return ToolOutput(tool_name="medicine_classifier", result=data, medicine_data=data)
```

**Gemini prompt design:**
- Never mentions prescribing
- Always returns structured JSON
- Does NOT use OCR — Gemini Vision natively understands the image
- `basic_safety_notes` is generic category-level info, never dosage

---

#### `app/tools/health_monitor_tool.py` — NEW

```python
# ── Threshold definitions ──────────────────────────────────────────
THRESHOLDS = {
    "systolic_bp":  {"normal": (90, 120), "warning": (120, 140), "danger": (140, 999)},
    "diastolic_bp": {"normal": (60, 80),  "warning": (80, 90),   "danger": (90, 999)},
    "sugar_fasting":{"normal": (70, 100), "warning": (100, 126),  "danger": (126, 999)},
    "weight_kg":    {"normal": (0, 999)},  # context-dependent, flag only rapid change
}

class HealthLogEntry(BaseModel):
    session_id: str
    condition: str        # "diabetes" | "hypertension" | "asthma" | "pregnancy" | "other"
    timestamp: str        # ISO format
    systolic_bp: Optional[int]
    diastolic_bp: Optional[int]
    sugar_fasting: Optional[float]
    sugar_postmeal: Optional[float]
    weight_kg: Optional[float]
    mood: Optional[str]   # "good" | "stressed" | "anxious" | "calm"
    symptoms: Optional[List[str]]
    notes: Optional[str]

class HealthAnalysisResult(BaseModel):
    summary: str
    flagged_readings: List[dict]
    diet_suggestions: List[str]
    lifestyle_recommendations: List[str]
    mental_health_guidance: str
    disclaimer: str

def log_health_entry(entry: HealthLogEntry, redis_db2: Redis) -> None:
    # append_health_log(redis_db2, session_id, entry.dict())

def analyze_health_trends(
    session_id: str,
    redis_db2: Redis,
    llm_client: LLMClient
) -> HealthAnalysisResult:
    # 1. logs = get_health_logs(redis_db2, session_id, limit=30)
    # 2. threshold_check(logs) → flagged_readings list
    # 3. Build structured text from logs + flagged readings
    # 4. ONE LLM call with HEALTH_ANALYSIS_PROMPT
    # 5. Parse JSON response → HealthAnalysisResult
    # 6. Always include disclaimer

def threshold_check(logs: List[dict]) -> List[dict]:
    # Iterate logs, compare each reading against THRESHOLDS
    # Return list of {timestamp, field, value, level: "warning"|"danger"}
```

---

#### `app/tools/consolidation_tool.py`
```python
def consolidate_disease_info(entities: dict, redis_db2: Redis, session_id: str) -> ToolOutput:
    # Pull conversation history from DB2
    # Build summary text of topics in the session
    # Return ToolOutput (LLM formats in aggregator)
```

---

### Phase 7 — TTS

---

#### `app/tts/kokoro_engine.py`
```python
class KokoroEngine:
    def __init__(self, lang_code: str = "a"):
        from kokoro import KPipeline
        self.pipeline = KPipeline(lang_code=lang_code)

    def synthesize(self, ssml_text: str, output_path: str) -> str:
        # Strip <speak> wrapper if needed
        # Generate WAV → save to output_path
        # Return output_path
```

---

### Phase 8 — API Layer

---

#### `app/api/routes.py` (UPDATED)
Three endpoints:

---

**`POST /api/process`** — Main voice/text pipeline (unchanged flow)

```
audio/text → VAD → STT → tone → intent → route → tools → DB2 update
→ aggregator (ONE LLM call) → SSML → TTS → JSON response
```

Response:
```python
class ProcessResponse(BaseModel):
    text_response: str
    audio_url: str
    tool_type: str
    map_data: Optional[dict] = None
    medicine_data: Optional[dict] = None   ← NEW
    latency_ms: int
    session_id: str
```

---

**`POST /api/classify-medicine`** — NEW Dedicated medicine classifier endpoint

```
Request: multipart/form-data
  - mode: "voice" | "text" | "image"
  - medicine_name: str     (for voice/text)
  - audio: file            (for voice — runs through STT first)
  - image: file            (for image — sent to Gemini Vision)
  - session_id: str

Flow:
  if mode == "voice": STT → extract medicine name → Gemini text classify
  if mode == "text":  medicine_name → Gemini text classify
  if mode == "image": image bytes → Gemini Vision → classify

  → Cache check/store (DB1)
  → Build SSML from result
  → TTS synthesis
  → Return MedicineClassifierResponse

Response:
{
  "medicine_name": "Paracetamol",
  "chemical_composition": "Acetaminophen 500mg",
  "drug_category": "Analgesic / Antipyretic",
  "purpose": "Relief of mild to moderate pain and fever",
  "basic_safety_notes": "Avoid alcohol. Do not exceed recommended dose.",
  "disclaimer": "Educational only. Consult a pharmacist or doctor.",
  "audio_url": "/static/audio/<uuid>.wav",
  "input_mode": "image",
  "session_id": "..."
}
```

---

**`POST /api/health-log`** — NEW Log a health reading

```
Request: JSON body
{
  "session_id": "...",
  "condition": "diabetes",
  "systolic_bp": 130,
  "diastolic_bp": 85,
  "sugar_fasting": 118,
  "weight_kg": 72.5,
  "mood": "stressed",
  "symptoms": ["headache", "fatigue"],
  "notes": "Did not sleep well"
}

Flow:
  → Validate with HealthLogEntry pydantic model
  → health_monitor_tool.log_health_entry() → append to DB2
  → Return: {"status": "logged", "timestamp": "..."}
```

---

**`GET /api/health-summary/{session_id}`** — NEW Trend analysis

```
Flow:
  → get_health_logs(redis_db2, session_id)
  → health_monitor_tool.analyze_health_trends()
  → Build SSML for voice summary
  → TTS synthesis
  → Return HealthAnalysisResult + audio_url
```

---

#### `app/api/health.py`
```python
GET /health
→ {
    "status": "ok",
    "redis_db1": true,
    "redis_db2": true,
    "timestamp": "2026-03-03T08:58:17Z"
  }
```

---

### Phase 9 — Utils

---

#### `app/utils/logger.py`
Structured logging using Python `logging` module.
Fields: `timestamp`, `level`, `module`, `event`, `duration_ms`, `session_id`

#### `app/utils/metrics.py`
```python
@dataclass
class RequestMetrics:
    stt_ms: int = 0
    intent_ms: int = 0
    tool_ms: int = 0
    llm_ms: int = 0
    tts_ms: int = 0
    cache_hit: bool = False

    @property
    def total_ms(self) -> int: ...
```

#### `app/utils/validators.py`
```python
ALLOWED_AUDIO_TYPES = ["audio/webm", "audio/wav", "audio/mpeg", "audio/ogg"]
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]     ← NEW
MAX_FILE_SIZE_MB = 10

def validate_audio_file(file: UploadFile) -> None
def validate_image_file(file: UploadFile) -> None    ← NEW
```

---

### Phase 10 — Frontend Changes

---

#### `src/types/clinical.ts` (UPDATED)

```typescript
export interface ApiResponse {
  text_response: string;
  audio_url: string;
  tool_type: string;
  map_data?: MapData;
  medicine_data?: MedicineData;    // NEW
  latency_ms: number;
  session_id: string;
}

export interface MapData {
  lat: number;
  lng: number;
  name: string;
  contact?: string;
}

// NEW
export interface MedicineData {
  medicine_name: string;
  chemical_composition: string;
  drug_category: string;
  purpose: string;
  basic_safety_notes: string;
  disclaimer: string;
  input_mode: "voice" | "text" | "image";
}

// NEW
export interface HealthLogEntry {
  condition: string;
  systolic_bp?: number;
  diastolic_bp?: number;
  sugar_fasting?: number;
  sugar_postmeal?: number;
  weight_kg?: number;
  mood?: string;
  symptoms?: string[];
  notes?: string;
}

// NEW
export interface HealthAnalysis {
  summary: string;
  flagged_readings: FlaggedReading[];
  diet_suggestions: string[];
  lifestyle_recommendations: string[];
  mental_health_guidance: string;
  disclaimer: string;
  audio_url?: string;
}

export interface FlaggedReading {
  timestamp: string;
  field: string;
  value: number;
  level: "warning" | "danger";
}

export type AppStatus = "idle" | "recording" | "processing" | "error" | "ready";

export const TOOL_LABELS: Record<string, string> = {
  medical_info: "Medical Info",
  medical_news: "Medical News",
  nearby_clinic: "Clinic Locator",
  medicine_classifier: "Medicine Classifier",     // replaces medicine_availability
  health_monitor_analysis: "Health Monitor",
  consolidation_summary: "Session Summary",
};

export interface ChatMessage {
  id: string;
  query: string;
  response: ApiResponse;
  timestamp: Date;
}
```

---

#### `src/App.tsx` (UPDATED)

```tsx
import HealthMonitorPage from "./pages/HealthMonitorPage";  // NEW

<Routes>
  <Route path="/"               element={<LandingPage />} />
  <Route path="/assistant"      element={<AssistantPage />} />
  <Route path="/data"           element={<DataPage />} />
  <Route path="/health-monitor" element={<HealthMonitorPage />} />  {/* NEW */}
  <Route path="*"               element={<NotFound />} />
</Routes>
```

---

#### `src/components/ChatInput.tsx` (UPDATED)

Add image upload button next to mic button.

```tsx
// NEW state
const [imageFile, setImageFile] = useState<File | null>(null);
const fileInputRef = useRef<HTMLInputElement>(null);

// NEW: sendImage function
const sendImage = async (file: File) => {
  onStatusChange("processing");
  const formData = new FormData();
  formData.append("mode", "image");
  formData.append("image", file);
  formData.append("session_id", sessionId);
  const res = await fetch("http://localhost:8000/api/classify-medicine", {
    method: "POST",
    body: formData
  });
  const data = await res.json();
  onStatusChange("ready");
  onResponse({ ...data, tool_type: "medicine_classifier" }, "[Image upload]");
};

// Added to JSX: camera/image upload icon button
// <input type="file" accept="image/*" ref={fileInputRef} ... />
// <button onClick={() => fileInputRef.current?.click()}>
//   <Camera className="w-5 h-5" />
// </button>
```

---

#### `src/components/ResponseCard.tsx` (UPDATED)

```tsx
// Add medicine_classifier case — renders MedicineClassifierCard
// Add health_monitor_analysis case — renders HealthSummaryCard
// Update toolIcons to include new tools

import MedicineClassifierCard from "./MedicineClassifierCard";
import HealthSummaryCard from "./HealthSummaryCard";

// Inside ResponseCard:
{data.tool_type === "medicine_classifier" && data.medicine_data && (
  <MedicineClassifierCard data={data.medicine_data} />
)}
```

---

#### `src/components/MedicineClassifierCard.tsx` — NEW

Displays the structured Gemini output in a clean card:

```tsx
interface Props {
  data: MedicineData;
}

// Renders:
// - Medicine name (prominent header)
// - Badge: drug_category
// - Row: Chemical Composition
// - Row: Purpose
// - Row: Basic Safety Notes
// - Disclaimer banner at bottom (amber/warning color)
// - Badge showing input_mode: "image" | "text" | "voice"
```

---

#### `src/pages/HealthMonitorPage.tsx` — NEW

Route: `/health-monitor`

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│  Header: "Long-Term Health Monitor"  Back → /         │
├────────────────────────┬─────────────────────────────┤
│   LEFT PANEL           │   RIGHT PANEL                │
│                        │                              │
│  HealthLogForm         │  HealthTrendChart            │
│  (condition selector,  │  (recharts line graphs       │
│   BP, sugar, weight,   │   for BP, sugar, weight)     │
│   mood, symptoms)      │                              │
│                        ├─────────────────────────────┤
│  [Log Reading] button  │  HealthSummaryCard           │
│                        │  (Analyze Trends button      │
│                        │   → GET /api/health-summary) │
│                        │                              │
│                        │  Shows: summary, flags,      │
│                        │  diet tips, lifestyle recs,  │
│                        │  mental health guidance,     │
│                        │  disclaimer, AudioPlayer)    │
└────────────────────────┴─────────────────────────────┘
```

**State managed:**
- `sessionId` — from localStorage or generated UUID
- `logs` — fetched history for chart
- `analysis` — result from `/api/health-summary`
- `condition` — selected condition type
- `isLogging / isAnalyzing` — loading states

---

#### `src/components/HealthLogForm.tsx` — NEW
```tsx
// Controlled form with fields:
// - condition: select (diabetes | hypertension | asthma | pregnancy | other)
// - systolic_bp: number input
// - diastolic_bp: number input
// - sugar_fasting: number input
// - sugar_postmeal: number input
// - weight_kg: number input
// - mood: radio/select (good | stressed | anxious | calm)
// - symptoms: multi-checkbox or tag input
// - notes: textarea
// On submit → POST /api/health-log
```

---

#### `src/components/HealthTrendChart.tsx` — NEW
```tsx
// Uses recharts LineChart
// Plots over time for selected metric:
//   - systolic_bp + diastolic_bp (dual line)
//   - sugar_fasting
//   - weight_kg
// Threshold reference lines (e.g. BP 140 = danger, 120 = warning)
// Tab switcher: BP | Sugar | Weight | Mood
```

---

#### `src/components/HealthSummaryCard.tsx` — NEW
```tsx
// Displays HealthAnalysis result:
// - summary paragraph
// - FlaggedReadings: colored badges (warning=amber, danger=red)
// - Diet Suggestions: bulleted list
// - Lifestyle Recommendations: bulleted list
// - Mental Health Guidance: italic paragraph
// - Disclaimer: prominent amber banner
// - AudioPlayer (for voice summary)
```

---

#### `src/hooks/useHealthMonitor.ts` — NEW
```typescript
export const useHealthMonitor = (sessionId: string) => {
  const logReading = async (entry: HealthLogEntry) => { ... }
  const getAnalysis = async () => { ... }
  const getLogs = useMemo(...)
  return { logReading, getAnalysis, logs, analysis, isLogging, isAnalyzing }
}
```

---

### Phase 11 — Tests

---

#### `tests/test_cache.py`
```
test_store_and_get_chunk()
test_ttl_expires()
test_append_context()
test_max_turns_trim()
test_append_health_log()            ← NEW
test_get_health_logs_limit()        ← NEW
```

---

#### `tests/test_mcp.py`
```
test_classify_medical_info()
test_classify_nearby_clinic()
test_classify_medicine_classifier()  ← NEW
test_router_routes_correctly()
```

---

#### `tests/test_tools.py`
```
test_medical_tool_cache_hit()
test_medical_tool_cache_miss()
test_news_tool_returns_articles()
```

---

#### `tests/test_medicine_classifier.py` — NEW
```
test_text_mode_cache_hit()
    → pre-populate DB1 → call classify_medicine(mode="text") → verify no Gemini call

test_text_mode_cache_miss()
    → mock GeminiClient → verify Gemini called → verify DB1 populated

test_image_mode_no_cache()
    → mock GeminiClient → verify Gemini Vision called → verify NOT cached in DB1

test_disclaimer_always_present()
    → for all modes, assert "disclaimer" in result

test_no_dosage_in_result()
    → verify "dosage" is NOT a key in returned JSON
    → verify "prescri" not in any string value (basic safety guard)

test_health_thresholds()
    → log BP 145/90 → analyze → verify flagged as "danger"
    → log BP 115/75 → analyze → verify no flags
```

---

## Complete Data Flow (Updated)

### Flow A — Main Voice/Text Query
```
POST /api/process (audio or text + session_id)
  → VAD → STT → ToneAnalysis
  → IntentClassifier (Groq) → one of:
      medical_info → OpenFDA + DB1 cache
      medical_news → NewsAPI + DB1 cache
      nearby_clinic → Google Maps
      medicine_classifier → Gemini + DB1 cache
      consolidation_summary → DB2 history
  → DB2 context update
  → ResponseAggregator (ONE final Groq call)
  → SSML Builder → Kokoro TTS
  → JSON { text_response, audio_url, tool_type, map_data?, medicine_data? }
```

### Flow B — Dedicated Medicine Classifier
```
POST /api/classify-medicine (mode + medicine_name/audio/image + session_id)
  → if voice: STT → medicine name
  → Cache check (DB1)
  → Gemini Vision (image) or Gemini Text (name)
  → Parse structured JSON
  → Cache store (if voice/text)
  → SSML → TTS
  → JSON { medicine_name, chemical_composition, drug_category, purpose,
           basic_safety_notes, disclaimer, audio_url, input_mode }
```

### Flow C — Health Monitor
```
POST /api/health-log (health parameters + session_id)
  → Validate HealthLogEntry
  → append_health_log(DB2)
  → Return { status: "logged", timestamp }

GET /api/health-summary/:session_id
  → get_health_logs(DB2, limit=30)
  → threshold_check() → flagged_readings
  → ONE Groq call (HEALTH_ANALYSIS_PROMPT)
  → SSML → TTS
  → JSON { summary, flagged_readings, diet_suggestions,
           lifestyle_recommendations, mental_health_guidance,
           disclaimer, audio_url }
```

---

## Implementation Order

```
1.  .env + requirements.txt + run.py
2.  config.py → dependencies.py → main.py
3.  redis_client.py → db1_cag.py → db2_context.py (with health log methods)
4.  prompts.py → formatter.py → client.py (Groq) → gemini_client.py
5.  vad.py → stt.py → tone_analysis.py → ssml_builder.py
6.  intent_classifier.py → router.py → response_aggregator.py
7.  medical_api_tool.py → news_tool.py → nearby_clinic_tool.py
8.  medicine_classifier_tool.py                     ← NEW TOOL
9.  health_monitor_tool.py                          ← NEW TOOL
10. consolidation_tool.py
11. kokoro_engine.py
12. health.py → routes.py                           ← all 4 endpoints
13. logger.py → metrics.py → validators.py
14. docker-compose.yml → redis.conf
15. types/clinical.ts                               ← frontend types first
16. App.tsx (add /health-monitor route)
17. MedicineClassifierCard.tsx
18. ChatInput.tsx (add image upload)
19. ResponseCard.tsx (handle new tool types)
20. HealthLogForm.tsx → HealthTrendChart.tsx → HealthSummaryCard.tsx
21. HealthMonitorPage.tsx → useHealthMonitor.ts
22. tests/
```

---

## Verification Checklist

### Backend
- [ ] `GET /health` → redis_db1 + redis_db2 both `true`
- [ ] `POST /api/process` with audio → returns `text_response` + `audio_url`
- [ ] `POST /api/process` (text: "what is diabetes") → `tool_type: "medical_info"`
- [ ] Same query again → `cache_hit: true` in logs, faster response
- [ ] `POST /api/process` (text: "find clinic near me") → `map_data` populated
- [ ] `POST /api/classify-medicine` (mode: text, paracetamol) → structured JSON returned
- [ ] `POST /api/classify-medicine` (mode: image, medicine strip) → Gemini vision result
- [ ] Verify `disclaimer` in every medicine classifier response
- [ ] Verify `dosage` never appears in medicine response
- [ ] `POST /api/health-log` → `{"status": "logged"}`
- [ ] Multiple logs → `GET /api/health-summary` → flagged readings for high BP
- [ ] SSML audio URL is playable

### Frontend
- [ ] `/assistant` — voice query works end to end
- [ ] `/assistant` — image upload button sends to `/api/classify-medicine`
- [ ] `MedicineClassifierCard` renders correctly for image mode
- [ ] `/health-monitor` route loads
- [ ] `HealthLogForm` submits successfully
- [ ] `HealthTrendChart` renders with logged data points
- [ ] `HealthSummaryCard` shows flagged warning in amber, danger in red
- [ ] Audio player works on health summary page
- [ ] Disclaimer is visible on both medicine and health pages

---

## Medical Disclaimer (Must appear on UI)

> ⚠️ **This system is not a medical device.** All information provided is for educational and
> informational purposes only. It does not constitute medical advice, diagnosis, or treatment.
> Always consult a qualified healthcare provider for any medical concerns.
