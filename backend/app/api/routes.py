# app/api/routes.py
# ── API Routes ─────────────────────────────────────────────────────
# Exposes the full pipeline endpoints:
#   POST /api/process          - Main voice+text pipeline (intent → MCP → LLM → TTS)
#   POST /api/classify-medicine - Dedicated medicine classifier (text/voice/image)
#   POST /api/health-log       - Log a health reading (Redis DB0 + Excel)
#   GET  /api/health-summary/{session_id} - AI health trend analysis + daily checklist
#   POST /api/health-chat      - Conversational chat about logged health data
#   GET  /api/medical-report/{session_id} - Generate a structured medical report
# Redis DB0 = conversation history & health logs
# Redis DB1 = tool retrieval cache (CAG)
import os
import time
from uuid import uuid4
from typing import Optional, List

from fastapi import APIRouter, Request, File, Form, UploadFile, HTTPException
from pydantic import BaseModel, Field

from app.voice import vad, stt, tone_analysis, ssml_builder
from app.mcp import intent_classifier, router as mcp_router, response_aggregator
from app.cache import db0_context
from app.cache.redis_client import redis_db0, redis_db1
from app.utils.validators import read_and_validate_audio, read_and_validate_image
from app.utils.metrics import RequestMetrics, record_latency
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger(__name__)
router = APIRouter()


# ── Health Log Deletion ───────────────────────────────────────────

@router.delete("/health-log/{session_id}/{chronic_disease:path}")
async def delete_disease_logs(session_id: str, chronic_disease: str):
    """Delete all health logs for a specific disease from Redis and Postgres."""
    from app.db.postgres import delete_health_logs_by_disease
    db0_context.delete_health_logs_by_disease(redis_db0, session_id, chronic_disease)
    delete_health_logs_by_disease(session_id, chronic_disease)
    return {"success": True, "message": f"Deleted logs for {chronic_disease}"}


# ── Doctor Advice Endpoints ────────────────────────────────────────

class DoctorAdviceRequest(BaseModel):
    session_id: str
    chronic_disease: str
    point: str

@router.post("/doctor-advice")
async def add_doctor_advice(body: DoctorAdviceRequest):
    """Store a doctor's advice point for a specific disease."""
    from app.db.postgres import insert_doctor_advice
    db0_context.append_doctor_advice(redis_db0, body.session_id, body.chronic_disease, body.point)
    insert_doctor_advice(body.session_id, body.chronic_disease, body.point)
    return {"success": True, "message": "Advice point added"}

@router.get("/doctor-advice/{session_id}/{chronic_disease:path}")
async def get_doctor_advice(session_id: str, chronic_disease: str):
    """Retrieve all doctor's advice points for a specific disease."""
    from app.db.postgres import get_doctor_advices_by_disease
    # Try Redis first
    points = db0_context.get_doctor_advices(redis_db0, session_id, chronic_disease)
    if not points:
        # Fallback to Postgres
        points = get_doctor_advices_by_disease(session_id, chronic_disease)
    return points

@router.delete("/doctor-advice/{session_id}/{chronic_disease:path}")
async def delete_doctor_advice(session_id: str, chronic_disease: str):
    """Clear all doctor's advice for a specific disease."""
    from app.db.postgres import delete_doctor_advices_by_disease
    db0_context.delete_doctor_advices(redis_db0, session_id, chronic_disease)
    delete_doctor_advices_by_disease(session_id, chronic_disease)
    return {"success": True, "message": "Advice cleared"}


# ── Response Schemas ───────────────────────────────────────────────

class ProcessResponse(BaseModel):
    text_response: str
    audio_url: str
    tool_type: str
    medicine_data: Optional[dict] = None
    report_data: Optional[dict] = None
    news_data: Optional[dict] = None
    map_data: Optional[dict] = None
    latency_ms: int
    session_id: str

class MedicineClassifierResponse(BaseModel):
    medicine_name: str
    chemical_composition: str
    drug_category: str
    purpose: str
    basic_safety_notes: str
    disclaimer: str
    input_mode: str
    audio_url: str
    session_id: str


from pydantic import BaseModel, Field

class HealthLogRequest(BaseModel):
    session_id: str
    condition: str = "other"
    chronic_disease: Optional[str] = None
    systolic_bp: Optional[int] = Field(None, ge=70, le=250)
    diastolic_bp: Optional[int] = Field(None, ge=40, le=150)
    sugar_fasting: Optional[float] = Field(None, ge=30, le=600)
    sugar_postmeal: Optional[float] = Field(None, ge=30, le=600)
    weight_kg: Optional[float] = Field(None, ge=10, le=500)
    mood: Optional[str] = None
    symptoms: Optional[list] = None
    notes: Optional[str] = None


# ── Helpers ────────────────────────────────────────────────────────

def _save_audio_file(kokoro_engine, ssml_text: str) -> str:
    """Synthesize TTS and save to static/audio. Returns relative URL."""
    filename = f"{uuid4()}.wav"
    output_path = os.path.join(settings.static_audio_dir, filename)
    kokoro_engine.synthesize(ssml_text, output_path)
    return f"/static/audio/{filename}"


# ── POST /api/process ──────────────────────────────────────────────

@router.post("/process", response_model=ProcessResponse)
async def process_query(request: Request):
    """
    Main pipeline: accepts voice (multipart) or text (JSON).

    Full flow:
    VAD → STT → Tone Analysis → Intent Classification
    → MCP Tool Routing → Redis Cache → LLM Response
    → SSML Formatting (per-intent tone) → TTS → Audio URL
    """
    metrics = RequestMetrics()
    session_id = str(uuid4())
    transcript = ""
    audio_bytes = None

    content_type = request.headers.get("content-type", "")
    user_lat: float | None = None
    user_lng: float | None = None

    # ── Parse input ────────────────────────────────────────────────
    if "multipart/form-data" in content_type:
        form = await request.form()
        audio_file = form.get("audio")
        session_id = form.get("session_id") or session_id
        _lat = form.get("lat")
        _lng = form.get("lng")
        if _lat and _lng:
            user_lat = float(_lat)
            user_lng = float(_lng)

        if audio_file and hasattr(audio_file, "read"):
            audio_bytes = await read_and_validate_audio(audio_file)

    elif "application/json" in content_type:
        body = await request.json()
        transcript = body.get("text", "").strip()
        session_id = body.get("session_id") or session_id
        user_lat = body.get("lat")
        user_lng = body.get("lng")
    else:
        raise HTTPException(status_code=400, detail="Unsupported content type")

    whisper_model = request.app.state.whisper_model
    kokoro_engine = request.app.state.kokoro_engine
    llm_client = request.app.state.llm_client
    gemini_client = request.app.state.gemini_client

    # ── Voice path: VAD + STT ──────────────────────────────────────
    if audio_bytes:
        t0 = time.perf_counter()
        try:
            audio_array = vad.process_audio(audio_bytes)
        except (vad.AudioTooLongError, vad.AudioTooShortError) as e:
            raise HTTPException(status_code=400, detail=str(e))

        stt_result = stt.transcribe(audio_array, whisper_model)
        transcript = stt_result.transcript
        metrics.stt_ms = int((time.perf_counter() - t0) * 1000)

    if not transcript:
        raise HTTPException(status_code=400, detail="No text or audio content provided")

    # ── Tone analysis ──────────────────────────────────────────────
    tone_result = tone_analysis.analyze_tone(transcript)

    # ── Intent classification → LLM ───────────────────────────────
    t0 = time.perf_counter()
    intent_result = intent_classifier.classify_intent(transcript, llm_client)
    metrics.intent_ms = int((time.perf_counter() - t0) * 1000)

    # ── Inject exact GPS coords into entities for nearby_clinic intent ──
    if intent_result.intent == "nearby_clinic" and user_lat and user_lng:
        intent_result.entities["lat"] = user_lat
        intent_result.entities["lng"] = user_lng
        logger.info(f"[GPS] Using exact coords: lat={user_lat}, lng={user_lng}")

    # ── MCP Tool Orchestration ─────────────────────────────────────
    t0 = time.perf_counter()
    tool_outputs = await mcp_router.route_to_tools(
        intent_result, redis_db1, redis_db0, session_id, gemini_client
    )
    metrics.tool_ms = int((time.perf_counter() - t0) * 1000)
    metrics.cache_hit = any(o.error is None and o.result for o in tool_outputs)

    # ── Context update (Redis DB0 — conversation history) ───────────────────
    db0_context.append_context(redis_db0, session_id, "user", transcript)
    context_history = db0_context.get_context(redis_db0, session_id)

    # ── LLM Response Generation ────────────────────────────────────
    t0 = time.perf_counter()
    text_response = response_aggregator.aggregate_response(
        tool_outputs, intent_result, context_history, llm_client
    )
    metrics.llm_ms = int((time.perf_counter() - t0) * 1000)

    db0_context.append_context(redis_db0, session_id, "assistant", text_response)

    # ── SSML Formatting: per-intent tone ──────────────────────────
    # medicine_info → informative | medical_news → neutral
    # medical_report → structured | health_monitoring → informative
    # general_conversation → neutral
    ssml_tone = response_aggregator.get_ssml_tone(intent_result.intent)
    t0 = time.perf_counter()
    ssml = ssml_builder.build_ssml(text_response, ssml_tone)

    # ── TTS Synthesis ──────────────────────────────────────────────
    audio_url = _save_audio_file(kokoro_engine, ssml)
    metrics.tts_ms = int((time.perf_counter() - t0) * 1000)

    record_latency(metrics, session_id)

    # Extract medicine / report data from tool outputs
    medicine_data = next((o.medicine_data for o in tool_outputs if o.medicine_data), None)
    report_data = next((o.report_data for o in tool_outputs if getattr(o, "report_data", None)), None)  # type: ignore[attr-defined]
    map_data = next((o.map_data for o in tool_outputs if getattr(o, "map_data", None)), None)
    # Extract news_data if the tool returned an articles result
    news_data = None
    if intent_result.intent == "medical_news":
        for o in tool_outputs:
            if o.result and isinstance(o.result, dict) and "articles" in o.result:
                news_data = o.result
                break

    return ProcessResponse(
        text_response=text_response,
        audio_url=audio_url,
        tool_type=intent_result.intent,
        medicine_data=medicine_data,
        report_data=report_data,
        news_data=news_data,
        map_data=map_data,
        latency_ms=metrics.total_ms,
        session_id=session_id,
    )


# ── POST /api/classify-medicine ────────────────────────────────────

@router.post("/classify-medicine", response_model=MedicineClassifierResponse)
async def classify_medicine_endpoint(
    request: Request,
    mode: str = Form(...),
    medicine_name: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
):
    """
    Dedicated medicine classifier endpoint.
    Modes: 'voice' → STT → Gemini text | 'text' → Gemini text | 'image' → Gemini Vision

    Returns: medicine name, category, purpose, safety notes + TTS audio.
    SSML tone: informative (educational delivery).
    """
    sid = session_id or str(uuid4())
    kokoro_engine = request.app.state.kokoro_engine
    gemini_client = request.app.state.gemini_client
    whisper_model = request.app.state.whisper_model

    image_bytes = None
    resolved_name = medicine_name

    if mode == "image" and image:
        image_bytes = await read_and_validate_image(image)

    elif mode == "voice" and audio:
        audio_bytes = await read_and_validate_audio(audio)
        audio_array = vad.process_audio(audio_bytes)
        stt_result = stt.transcribe(audio_array, whisper_model)
        resolved_name = stt_result.transcript

    from app.tools.medicine_classifier_tool import classify_medicine
    tool_output = classify_medicine(
        input_mode=mode,
        medicine_name=resolved_name,
        image_bytes=image_bytes,
        redis_db1=redis_db1,
        gemini_client=gemini_client,
    )

    data = tool_output.medicine_data or tool_output.result

    # Build TTS using informative tone (medicine explanation)
    voice_text = (
        f"{data.get('medicine_name', 'This medicine')} is a "
        f"{data.get('drug_category', 'medication')}. "
        f"It is used for {data.get('purpose', 'therapeutic purposes')}. "
        f"{data.get('basic_safety_notes', '')} "
        f"Please consult a pharmacist for personal advice."
    )
    ssml = ssml_builder.build_ssml(voice_text, "informative")
    audio_url = _save_audio_file(kokoro_engine, ssml)

    return MedicineClassifierResponse(
        medicine_name=data.get("medicine_name", "Unknown"),
        chemical_composition=data.get("chemical_composition", ""),
        drug_category=data.get("drug_category", ""),
        purpose=data.get("purpose", ""),
        basic_safety_notes=data.get("basic_safety_notes", ""),
        disclaimer=data.get("disclaimer", ""),
        input_mode=mode,
        audio_url=audio_url,
        session_id=sid,
    )


# ── POST /api/health-log ───────────────────────────────────────────

@router.post("/health-log")
async def log_health(entry: HealthLogRequest):
    """
    Log a health reading to Redis DB0 (conversation history), Excel, and Postgres.
    Supports: blood pressure, blood sugar, weight, mood, symptoms, notes.
    """
    from app.tools.health_monitor_tool import HealthLogEntry, log_health_entry
    from app.db.postgres import insert_health_log
    
    health_entry = HealthLogEntry(**entry.model_dump())
    log_health_entry(health_entry, redis_db0)
    
    # Also save to Postgres for long-term persistence
    insert_health_log(entry.model_dump())
    
    return {"status": "logged", "session_id": entry.session_id}

@router.get("/health-log/{session_id}")
async def get_health_logs(session_id: str, chronic_disease: Optional[str] = None):
    """
    Fetch persistent health logs for a session from the Postgres database.
    Optionally filters by chronic disease context.
    """
    from app.db.postgres import get_health_logs_by_session
    logs = get_health_logs_by_session(session_id, chronic_disease)
    return logs


# ── GET /api/health-summary/{session_id} ──────────────────────────

@router.get("/health-summary/{session_id}")
async def get_health_summary(session_id: str, request: Request, chronic_disease: Optional[str] = None):
    """
    Retrieve AI trend analysis + daily checklist for a session's health logs.
    Optionally filters logs by chronic disease context.
    """
    health_llm_client = request.app.state.health_llm_client
    kokoro_engine = request.app.state.kokoro_engine

    from app.tools.health_monitor_tool import analyze_health_trends
    analysis = analyze_health_trends(session_id, redis_db0, health_llm_client, chronic_disease)

    # TTS summary using informative tone
    summary_text = analysis.get("summary", "No trends detected yet.")
    ssml = ssml_builder.build_ssml(summary_text, "informative")
    audio_url = _save_audio_file(kokoro_engine, ssml)

    analysis["audio_url"] = audio_url
    analysis["session_id"] = session_id
    return analysis


# ── GET /api/medical-report/{session_id} ──────────────────────────

@router.get("/medical-report/{session_id}")
async def get_medical_report(session_id: str, request: Request, chronic_disease: Optional[str] = None):
    """
    Generate a structured medical report from stored user data.

    Pulls:
    - Detailed logs (for graphs/tables)
    - 6 Clinical Tips (via Health LLM)

    Returns a structured report dict + TTS audio.
    """
    from app.tools.report_tool import generate_medical_report
    kokoro_engine = request.app.state.kokoro_engine
    health_llm_client = request.app.state.health_llm_client

    tool_output = generate_medical_report(
        session_id=session_id, 
        redis_db0=redis_db0, 
        health_llm=health_llm_client,
        chronic_disease=chronic_disease
    )
    report = tool_output.report_data or tool_output.result

    # Build voice summary
    if report.get("has_health_data"):
        logs_count = len(report.get("detailed_logs", []))
        disease = report.get("chronic_disease", "your condition")
        voice_text = (
            f"I have generated your personalized health report for {disease}. "
            f"It includes a summary of your {logs_count} logged readings and six clinical tips to help you manage your health. "
            f"Please review the detailed data and charts on your dashboard."
        )
    else:
        voice_text = (
            "Your health report is currently empty. "
            "Please log some health readings first so I can analyze your trends and provide tips."
        )

    ssml = ssml_builder.build_ssml(voice_text, "structured")
    audio_url = _save_audio_file(kokoro_engine, ssml)

    report["audio_url"] = audio_url
    return report


# ── POST /api/health-chat ──────────────────────────────────────────

class HealthChatRequest(BaseModel):
    session_id: str
    message: str
    chronic_disease: Optional[str] = None


class HealthChatResponse(BaseModel):
    response: str
    audio_url: str
    session_id: str


@router.post("/health-chat", response_model=HealthChatResponse)
async def health_chat(body: HealthChatRequest, request: Request):
    """
    Conversational chat about the user's own health logs.

    Retrieves health history from Redis DB0 and uses it as LLM context.
    Returns a text insight + TTS audio (informative SSML tone).
    """
    import json
    from app.llm.prompts import HEALTH_CHAT_PROMPT
    from app.llm.formatter import strip_markdown, truncate_response

    health_llm_client = request.app.state.health_llm_client
    kokoro_engine = request.app.state.kokoro_engine

    # ── Pull health logs from DB0 (history) ───────────────────────────
    logs = db0_context.get_health_logs(redis_db0, body.session_id, limit=20)
    chat_history = db0_context.get_context(redis_db0, f"healthchat:{body.session_id}")

    logs_text = (
        json.dumps(logs, indent=None)[:2000]
        if logs
        else "No health readings have been logged yet for this session."
    )

    # Extract chronic disease from the frontend request directly, or fallback to the most recent log
    chronic_disease = body.chronic_disease or "None specified"
    if chronic_disease == "None specified" and logs and "chronic_disease" in logs[-1] and logs[-1]["chronic_disease"]:
        chronic_disease = logs[-1]["chronic_disease"]

    messages = [
        {
            "role": "system",
            "content": (
                f"{HEALTH_CHAT_PROMPT}\n\n"
                f"=== CRITICAL PATIENT INFO ===\n"
                f"THE USER HAS ALREADY DECLARED THEIR CHRONIC CONDITION IS: {chronic_disease}\n"
                f"Always base your advice on {chronic_disease}.\n"
                f"If they ask what their condition is, you MUST tell them it is {chronic_disease}.\n"
                f"==========================\n\n"
                f"USER'S HEALTH LOG DATA:\n{logs_text}"
            ),
        }
    ]

    for turn in chat_history[-6:]:
        messages.append({"role": turn["role"], "content": turn["content"]})

    messages.append({"role": "user", "content": body.message})

    raw = health_llm_client.chat(messages, max_tokens=1000)
    ai_response = truncate_response(strip_markdown(raw), max_chars=2500)

    # ── Persist chat turns to DB0 (history) ───────────────────────────
    chat_key = f"healthchat:{body.session_id}"
    db0_context.append_context(redis_db0, chat_key, "user", body.message, max_turns=20)
    db0_context.append_context(redis_db0, chat_key, "assistant", ai_response, max_turns=20)

    # ── TTS (informative tone for health conversations) ────────────
    ssml = ssml_builder.build_ssml(ai_response, "informative")
    audio_url = _save_audio_file(kokoro_engine, ssml)

    logger.info(f"Health chat response for session {body.session_id}")

    return HealthChatResponse(
        response=ai_response,
        audio_url=audio_url,
        session_id=body.session_id,
    )


# ── GET /api/conversation-history/{session_id} ────────────────────

@router.get("/conversation-history/{session_id}")
async def get_conversation_history(session_id: str):
    """
    Retrieve conversation history for a session from Redis DB0.
    Used by frontend to restore chat history after page refresh.
    
    Returns:
    - messages: list of conversation turns (role, content)
    - session_id: the session identifier
    - has_history: boolean indicating if history exists
    """
    try:
        history = db0_context.get_context(redis_db0, session_id)
        
        return {
            "messages": history,
            "session_id": session_id,
            "has_history": len(history) > 0,
        }
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation history")
