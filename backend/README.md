# 🏥 Voice AI Healthcare Assistant — Backend

> **Capstone Project** | AI-powered voice-enabled healthcare assistant backend  
> Built with FastAPI · Faster-Whisper · Groq LLM · Gemini Vision · Kokoro TTS · Redis

---

## 📋 Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Running the Server](#running-the-server)
- [API Endpoints](#api-endpoints)
- [Tool Pipeline (MCP)](#tool-pipeline-mcp)
- [Caching Strategy](#caching-strategy)
- [SSML & TTS](#ssml--tts)
- [Testing](#testing)
- [Health Monitoring Module](#health-monitoring-module)

---

## Overview

A **voice-first healthcare assistant** that accepts microphone input or text, classifies the user's intent using an LLM, routes it to the appropriate tool, generates a contextual response, and returns both text and synthesized audio.

The system is modular, with each component isolated into its own layer:

```
Voice/Text Input → STT → Intent Classification → MCP Tool Routing
     → Redis Cache → LLM Response → SSML Formatting → TTS Audio
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT LAYER                              │
│     Voice (WebM/Opus)    ──►  Faster-Whisper STT               │
│     Text (JSON)          ──►  Direct                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   INTENT CLASSIFICATION                         │
│         Groq LLM → 5 Intents (medicine_info, medical_news,     │
│         medical_report, health_monitoring, general_conversation)│
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              MCP — MODEL CONTROL PLANE (router.py)              │
│   Routes intent → Tool → Redis Cache (DB1) → Tool Output       │
│                                                                 │
│  ┌──────────────┐  ┌────────────┐  ┌───────────┐  ┌────────┐  │
│  │medicine_info │  │medical_news│  │med_report │  │health  │  │
│  │Gemini Vision │  │NewsAPI     │  │Redis DB2  │  │monitor │  │
│  └──────────────┘  └────────────┘  └───────────┘  └────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   RESPONSE AGGREGATION                          │
│         Groq LLM → Text Response (≤ 3 sentences for TTS)       │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              SSML + TTS LAYER                                   │
│   Per-intent SSML prosody → Kokoro TTS → WAV audio file        │
│   informative / neutral / structured / alert                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features

| Feature | Description |
|---------|-------------|
| 🎙️ **Voice Input** | Browser microphone → WebM/Opus → Faster-Whisper STT |
| 💊 **Medicine Classifier** | Text or image input → Gemini Vision → drug info card |
| 📰 **Medical News** | Fetches latest pharma/healthcare news via NewsAPI |
| 📋 **Medical Report** | Generates structured report from session history & health logs |
| ❤️ **Health Monitoring** | Logs BP, sugar, weight, mood; AI trend analysis + daily checklist |
| 🔊 **Expressive TTS** | Kokoro TTS + SSML prosody control per intent type |
| 🗄️ **Redis Caching** | DB1 (tool responses CAG) + DB2 (session context + health logs) |
| 📊 **Excel Export** | Health readings auto-exported to `.xlsx` per session |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Web Framework | FastAPI + Uvicorn |
| Speech-to-Text | Faster-Whisper (`base` model) |
| Audio Decoding | PyAV (ffmpeg — handles WebM/Opus) |
| LLM (Intent + Response) | Groq API (`llama-3.3-70b-versatile`) |
| LLM (Medicine Vision) | Google Gemini (`gemini-1.5-flash`) |
| Text-to-Speech | Kokoro TTS (local) |
| Caching | Redis (Docker) — DB1 + DB2 |
| News | NewsAPI |
| Medical Data | OpenFDA API |
| Data Persistence | Redis + Excel (openpyxl) |
| Validation | Pydantic v2 |
| Testing | pytest + pytest-asyncio + fakeredis |

---

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── routes.py          # All API endpoints
│   │   └── health.py          # Health check + Redis debug endpoints
│   ├── mcp/
│   │   ├── intent_classifier.py   # 5-intent LLM classifier
│   │   ├── router.py              # MCP tool routing
│   │   └── response_aggregator.py # Per-intent SSML tone + LLM response
│   ├── tools/
│   │   ├── medicine_classifier_tool.py   # Tool 1: Medicine info
│   │   ├── news_tool.py                  # Tool 2: Medical news
│   │   ├── report_tool.py               # Tool 3: Medical report (NEW)
│   │   ├── health_monitor_tool.py       # Health module (Excel + checklist)
│   │   └── medical_api_tool.py          # OpenFDA integration
│   ├── cache/
│   │   ├── redis_client.py    # DB1 + DB2 Redis connections
│   │   ├── db1_cag.py         # Tool response cache (CAG)
│   │   └── db2_context.py     # Session context + health logs
│   ├── voice/
│   │   ├── stt.py             # Faster-Whisper transcription
│   │   ├── vad.py             # Voice activity detection (PyAV decoder)
│   │   └── ssml_builder.py    # SSML per-tone formatter
│   ├── llm/
│   │   ├── client.py          # Groq LLM client (with retry)
│   │   ├── gemini_client.py   # Gemini Vision client
│   │   ├── prompts.py         # All centralized LLM prompts
│   │   └── formatter.py       # Strip markdown, extract JSON
│   ├── tts/
│   │   └── kokoro_engine.py   # Kokoro TTS engine
│   ├── utils/
│   │   ├── logger.py          # Structured JSON logger
│   │   ├── metrics.py         # Request latency tracking
│   │   └── validators.py      # Audio/image file validators
│   ├── main.py                # FastAPI app + lifespan events
│   └── config.py              # Pydantic settings (reads .env)
├── tests/
│   ├── test_cache.py          # Redis DB1/DB2 layer tests
│   ├── test_mcp.py            # Intent classifier + router tests
│   └── test_tools.py          # Medicine classifier + health monitor tests
├── docker/
│   ├── docker-compose.yml     # Redis container setup
│   └── redis.conf             # Redis configuration
├── health_data/               # Excel health exports (auto-created)
├── static/audio/              # TTS WAV files (auto-created)
├── .env                       # Secret keys (never commit!)
├── .env.example               # Template for environment setup
├── .gitignore
├── requirements.txt
└── run.py                     # Uvicorn entrypoint
```

---

## Setup & Installation

### Prerequisites

- Python 3.10+ (Anaconda/venv recommended)
- Docker Desktop (for Redis)
- Node.js 18+ (for frontend)

### 1. Clone the repository

```bash
git clone https://github.com/kamaleshct118/Voice_Capstone.git
cd Voice_Capstone/backend
```

### 2. Create and activate virtual environment

```bash
conda create -n venv python=3.10
conda activate venv
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

### 5. Start Redis (Docker)

```bash
cd docker
docker compose up -d
cd ..
```

### 6. Start the backend

```bash
python run.py
```

Server starts at: **http://localhost:8000**  
API Docs (Swagger): **http://localhost:8000/docs**

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq LLM API key ([console.groq.com](https://console.groq.com)) | ✅ |
| `LLM_MODEL` | Groq model name (`llama-3.3-70b-versatile`) | ✅ |
| `GEMINI_API_KEY` | Google Gemini API key ([aistudio.google.com](https://aistudio.google.com)) | ✅ |
| `NEWS_API_KEY` | NewsAPI key ([newsapi.org](https://newsapi.org)) | ✅ |
| `REDIS_HOST` | Redis host (default: `localhost`) | ✅ |
| `REDIS_PORT` | Redis port (default: `6379`) | ✅ |
| `WHISPER_MODEL_SIZE` | Whisper model size (`tiny`, `base`, `small`) | ✅ |
| `STATIC_AUDIO_DIR` | Audio file output directory | ✅ |
| `HEALTH_EXCEL_DIR` | Excel health export directory | ✅ |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | ✅ |

---

## Running the Server

```bash
# Development (auto-reload on file changes)
python run.py

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/process` | Main pipeline: voice or text → LLM → TTS |
| `POST` | `/api/classify-medicine` | Medicine classifier (text / voice / image) |
| `POST` | `/api/health-log` | Log a health reading (Redis + Excel) |
| `GET` | `/api/health-summary/{session_id}` | AI trend analysis + daily checklist |
| `GET` | `/api/medical-report/{session_id}` | Generate structured health report |
| `POST` | `/api/health-chat` | Conversational chat about health logs |
| `GET` | `/health` | Liveness probe (Redis ping) |
| `GET` | `/api/redis/db1` | Debug: inspect CAG cache |
| `GET` | `/api/redis/db2` | Debug: inspect context + health logs |

### POST `/api/process` — Request

**Voice (multipart/form-data):**
```
audio: <audio blob>
session_id: <uuid>
```

**Text (application/json):**
```json
{ "text": "Tell me about ibuprofen", "session_id": "abc-123" }
```

### POST `/api/process` — Response

```json
{
  "text_response": "Ibuprofen is a nonsteroidal anti-inflammatory drug...",
  "audio_url": "/static/audio/abc123.wav",
  "tool_type": "medicine_info",
  "medicine_data": { "medicine_name": "Ibuprofen", "drug_category": "NSAID", ... },
  "report_data": null,
  "latency_ms": 1823,
  "session_id": "abc-123"
}
```

---

## Tool Pipeline (MCP)

The **Model Control Plane** routes each intent to the correct tool:

| Intent | Tool | Cache |
|--------|------|-------|
| `medicine_info` | `medicine_classifier_tool.py` (Gemini) | DB1 — 24h |
| `medical_news` | `news_tool.py` (NewsAPI) | DB1 — 1h |
| `medical_report` | `report_tool.py` (Redis DB2 history) | None |
| `health_monitoring` | `health_monitor_tool.py` (Redis DB2) | None |
| `general_conversation` | *(no tool — direct LLM)* | None |

---

## Caching Strategy

| Redis DB | Purpose | TTL |
|----------|---------|-----|
| **DB1** — CAG Cache | Tool response cache (medicine, news) | 1h – 24h |
| **DB2** — Context Cache | Conversation history, health logs, chat turns | Session |

Cache key format: `SHA256(intent + normalized_query)[:16]`

---

## SSML & TTS

Every LLM response is converted to SSML before being sent to Kokoro TTS.  
Prosody is adjusted per intent:

| Tone | Rate | Pitch | Intent |
|------|------|-------|--------|
| `informative` | medium | +0st | `medicine_info`, `health_monitoring` |
| `neutral` | medium | +0st | `medical_news`, `general_conversation` |
| `structured` | slow | -1st | `medical_report` |
| `alert` | slow | -2st | Emergency health flags |

---

## Testing

Tests use **fakeredis** (no real Redis needed) and **unittest.mock** (no real API calls).

```bash
# Activate venv first
conda activate venv

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_cache.py -v
python -m pytest tests/test_mcp.py -v
python -m pytest tests/test_tools.py -v

# Run with logs visible
python -m pytest tests/ -v -s
```

**Test coverage:**

| File | Tests | What's covered |
|------|-------|----------------|
| `test_cache.py` | 10 | DB1 CAG cache, DB2 context, health logs, TTL |
| `test_mcp.py` | 12 | All 5 intents, fallback, router routing |
| `test_tools.py` | 11 | Medicine classifier (cache hit/miss), health thresholds |

---

## Health Monitoring Module

The health dashboard lets users log daily vitals and get AI-driven insights:

### Logging a reading

```bash
curl -X POST http://localhost:8000/api/health-log \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc-123",
    "condition": "hypertension",
    "systolic_bp": 138,
    "diastolic_bp": 88,
    "sugar_fasting": 105,
    "mood": "tired"
  }'
```

### Getting analysis + daily checklist

```bash
curl http://localhost:8000/api/health-summary/abc-123
```

**Response includes:**
- `summary` — AI trend overview
- `flagged_readings` — BP/sugar readings above safe thresholds
- `diet_suggestions` — Personalized diet tips
- `lifestyle_recommendations` — Exercise & habits
- `daily_checklist` — AI-generated daily task list
- `audio_url` — TTS voice summary

### Data persistence

- **Redis DB2** — In-session fast access (up to 30 entries per session)
- **Excel file** — `health_data/health_<session_id[:8]>.xlsx` (permanent record)

---

## Medical Disclaimer

> This application is for **educational and personal tracking purposes only**.  
> It does **not** provide medical advice, diagnosis, or treatment.  
> Always consult a qualified healthcare provider for any health concerns.

---

## License

MIT License — Capstone Project 2026
