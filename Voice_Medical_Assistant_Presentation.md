# 🏥 Voice AI Healthcare Assistant - Capstone Presentation Guide

## 1. Complete Project Flow in Detail
The Voice Medical Assistant v3.0 acts as an advanced health assistant capable of receiving voice inputs, retaining context through a sophisticated memory structure, handling multimodal queries, and monitoring patient health parameters over the long term. 

### Data Breakdown Pipeline
1. **User Interaction**: Users interact using natural voice commands or by uploading images (e.g., a photo of a prescription bottle). The frontend sends raw audio chunks (WebM/Opus) or Base64 images directly to the backend.
2. **Voice Capture & VAD Layer**: A Voice Activity Detector (VAD) instantly filters out background noise and silence to reduce latency.
3. **Transcription (STT)**: `faster-whisper` transcribes speech to text locally using an optimized compute pattern.
4. **Intent Recognition (MCP - Model Control Plane)**: The Groq LLM (Llama 3) functions as a high-speed orchestrator, analyzing the transcript to identify the underlying user intent (e.g., medicine info, health monitoring) and extract entities.
5. **Cache-Augmented Retrieval (CAG)**: Before executing expensive tools, the system checks **Redis DB1**. If a tool response for the exact intent/entities was recently cached, it's served instantly.
6. **Agentic Tool Execution**: If no cache is found, specialized tools are executed concurrently:
   - *Health Monitor*: Normalizes and logs vitals to PostgreSQL.
   - *Clinic Finder*: Queries Overpass API for nearby hospitals.
   - *Medicine Classifier*: Uses Gemini Vision to parse pill images.
   - *Medical News & API*: Fetches health news or medical drug info.
7. **Context & Persistence**: **Redis DB0** maintains continuous conversation memory, ensuring context is kept across turns. **PostgreSQL** stores long-term health metrics permanently.
8. **Response Aggregation**: A separate LLM layer reformulates the raw tool data into a compassionate, medically-informed narrative response.
9. **Synthesis (TTS)**: The Kokoro Engine converts the text into natural-sounding speech audio (PCM 16-bit) and streams it back to the frontend in chunks. Co-occurring UI payloads trigger dynamic React components (maps, charts).

---

## 2. Codebase Structure
The codebase architecture follows a modular pipeline designed for high-concurrency workflows:
- `backend/app/api`: Handles FastAPI routes for processing streams.
- `backend/app/cache`: Manages Redis logic (`db0_context.py`, `db1_cag.py`).
- `backend/app/core`: Core utilities like device assignment (`cpu`/`cuda`).
- `backend/app/db`: PostgreSQL integration, schema definitions.
- `backend/app/llm`: Groq and Gemini clients for fast NLP tasks.
- `backend/app/mcp`: The orchestrator handling intent classification and routing requests to tools.
- `backend/app/tools`: Houses the core clinical agent tools (medicine classifier, health monitor, etc.).
- `backend/app/voice` & `backend/app/tts`: Speech transcription (Whisper) and generation (Kokoro).

---

## 3. Models Used: Justification & Advantages
**1. Automatic Speech Recognition (STT) - Faster-Whisper**
- **Why It's Used**: Highly accurate speech-to-text specifically tuned for English.
- **Advantages**: By deploying CTranslate2 in integer quantization, it runs locally at exceptional speeds without cloud roundtrip latency, protecting crucial patient audio privacy via localized processing.

**2. Intelligent Orchestration (LLM) - Groq (Llama-3.1 & Llama-3.3)**
- **Why It's Used**: To control agentic tool routing and generate compassionate responses.
- **Advantages**: Groq delivers inference through Language Processing Units (LPUs) at blistering speeds. This drops TTFB (Time-To-First-Byte) to minimal MS latency, which is essential for true zero-delay voice emulation.

**3. Multimodal Analysis - Google Gemini Vision (gemini-2.0-flash)**
- **Why It's Used**: Superior spatial OCR and context image comprehension.
- **Advantages**: Accurately processes complex pharmaceutical labels and identifies pills/packaging even in skewed photographs. Excellent multi-step instruction following.

**4. Medical Reports - Health LLM (GPT-4o / Internal)**
- **Why It's Used**: Tailored API endpoint for clinical understanding.
- **Advantages**: Produces highly structured, medically sound summaries and advice reports based on accumulated dataset vitals.

**5. Text-To-Speech (TTS) - Kokoro**
- **Why It's Used**: Extremely lightweight yet highly emotive neural TTS.
- **Advantages**: Handles chunked generative audio streaming flawlessly. The `af_heart` phonetic profile natively models a warm, empathetic clinical tone.

---

## 4. Model Parameters Reference
*Properly tuning AI behavior is vital for speed and safety. The following parameters dictate system execution:*

### Faster-Whisper (STT)
- `model_size`: `"distil-whisper/distil-small.en"`
- `beam_size`: `1` (Employs fast deterministic decoding rather than heavy search trees).
- `language`: `None` (Model auto-detects English inherently).
- `vad_filter`: `False` (Silence filtering is handled explicitly by our custom UI/Pre-processor to save ML memory).
  
### Groq LLM (Orchestrator)
- `model`: `"llama-3.1-8b-instant"` (Handles default intent routing).
- `compression_model`: `"llama-3.3-70b-versatile"` (Used for intense context summarization).
- `temperature`: `0.3` (A low temperature grounds the AI firmly, reducing hallucinations and keeping instructions strictly clinical).
- `max_tokens`: `200` (Caps response duration, forcing the assistant to be concise which drastically saves on TTS audio load time).
- `timeout`: `30s` (Prevents stale network calls from locking the system).
  
### Gemini Vision
- `model`: `"gemini-2.0-flash"`
- **Pre-processing Metric**: Incoming images are strictly clamped and resized to `(1024, 1024)` before inference, balancing token ingestion limits with accurate OCR fidelity.
  
### Kokoro Engine (TTS)
- `voice`: `"af_heart"`
- `lang_code`: `"a"` (American English mapping).
- `samplerate`: `24000` (Standard 24kHz for voice reproduction).
- `subtype`: `"PCM_16"` (Direct generation to uncompressed 16-bit Float for flawless frontend playing).

---

## 5. Extensive Database Schema
The database architecture uses a dual-pronged approach: permanent durability (Postgres) and rapid volatility (Redis).

### PostgreSQL Schema (Persistent Storage)
Serves as the HIPAA-compliant datastore for permanent patient vitals.
- **Table: `health_logs`**
  - `id` (SERIAL PRIMARY KEY)
  - `session_id` (VARCHAR) - Ties history to the specific user/session.
  - `timestamp` (TIMESTAMPTZ)
  - `condition` (VARCHAR)
  - `chronic_disease` (VARCHAR) - Groups data points (e.g., "Diabetes", "Hypertension").
  - `systolic_bp` / `diastolic_bp` (INT)
  - `sugar_fasting` / `sugar_postmeal` (FLOAT)
  - `weight_kg` (FLOAT)
  - `mood` (VARCHAR)
  - `symptoms` (TEXT[])
  - `notes` (TEXT)
- **Table: `doctor_advice`**
  - `id` (SERIAL PRIMARY KEY)
  - `session_id` (VARCHAR)
  - `chronic_disease` (VARCHAR)
  - `point` (TEXT) - The doctor's specific guidance.
  - `timestamp` (TIMESTAMPTZ)

### Redis Cache Scheme (Temporary Context & Tool Caching)
- **Redis DB0 (Conversation Context & Volatile Health Arrays)**:
  - `ctx:{session_id}`: Keeps a rolling history of `role/content` logs (TTL: 30 hours). Once the conversation hits a cap (10 turns), the LLM dynamically compresses the history to save tokens.
  - `health:{session_id}`: Temporarily caches recent health reading objects prior to DB retrieval.
  - `advice:{session_id}:{chronic_disease}`: Rapid fetching of medical advice.
- **Redis DB1 (Cache-Augmented Generation / CAG)**:
  - Cache Keys are generated via SHA-256 hash formatting (`hashlib.sha256(f"{intent}:{query.lower().strip()}")`).
  - Holds direct Tool outputs to prevent executing duplicate LLM/API calls on identical conversational questions.
  - TTL duration (Drug/News/Medicine queries): 36 Hours.

---

## 6. Voice AI Systems Detailed Explanation
The Voice pipeline represents an optimized, bidirectional low-latency setup engineered specifically for clinical interactions:
1. **Intelligent Intake**: Audio hits the server in Opus/PCM chunks. A Voice Activity Detector (VAD) drops empty noise buffers instantly to conserve compute cycles.
2. **Memory-Mapped Transcription**: `stt.py` (`faster-whisper`) interprets the arrays and maps confidence scores (deriving from Average Log Probability limits). If transcription confidence drops below a threshold, the system re-prompts the patient.
3. **Sequential Chunk Synthesis**: `kokoro_engine.py` doesn't wait for the text to finish. It takes the LLM's raw text and converts it into continuous `PCM 16-bit` arrays via standard python `yield` looping.
4. **VRAM Optimization**: Tensor memory on physical GPUs is aggressively garbage-collected (`free_gpu_cache()`) between TTS payloads. This guarantees stability for production instances running on 4GB-8GB GPU limits during consecutive query streams.
5. **Architectural Future-Proofing**: The engine supports migrating away from large multipart HTTP chunks towards **Full WebSockets streaming**, ensuring that audio frames reach the browser client milliseconds after LLM token generation.

---

## 7. Tool Implementations (The Clinical Engine Array)
1. **Medicine Classifier (`medicine_classifier_tool.py`)**: Utilizes Gemini to extract generic names, categories, and safety notes from packaging. Fails-safes gracefully into pure text-question pipelines if OCR yields no imagery inputs. Constrains responses to 100 words dynamically.
2. **Health Monitor (`health_monitor_tool.py`)**: Extracts raw conversational numbers (e.g. "my BP went up to 120 over 80 last night") and maps them to fixed integers for Postgres insertion, rendering them queryable.
3. **Clinic Finder (`nearby_clinic_tool.py`)**: Interfaces with the Overpass JSON API to execute geospatial proximity logic, emitting both voice instructions and coordinates for React mapping rendering.
4. **Medical Database (`medical_api_tool.py`)**: Hooks into OpenFDA resources for live updates on medical side effects and pharmaceutical classifications.
5. **Medical News (`news_tool.py`)**: Gathers and filters news feeds targeting latest health alerts.
6. **Report Engine (`report_tool.py`)**: Aggregates data from the Postgres DBs to construct localized clinical summaries for actual physician reviews.
