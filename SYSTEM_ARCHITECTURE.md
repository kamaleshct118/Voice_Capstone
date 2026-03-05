# Voice AI Healthcare Assistant - Complete System Architecture

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Tool Descriptions](#tool-descriptions)
4. [System Prompts](#system-prompts)
5. [Data Flow](#data-flow)
6. [Redis Database Structure](#redis-database-structure)
7. [Intent Classification](#intent-classification)
8. [Response Aggregation](#response-aggregation)

---

## System Overview

**Voice AI Healthcare Assistant v3.0** is a multimodal voice-orchestrated clinical intelligence system featuring:
- Gemini-based medicine classification (text + image)
- Cache-Augmented Generation (CAG) with Redis
- Context-aware conversation memory
- Long-term health monitoring with Excel export
- Real-time medical news and FDA drug information
- Nearby clinic/hospital search with GPS precision
- Text-to-Speech with SSML tone control (Kokoro TTS)
- Speech-to-Text with Whisper (distil-small.en)

**Tech Stack:**
- Backend: FastAPI (Python 3.11+)
- Frontend: React + TypeScript + Vite
- LLM: Groq (Llama 3.3 70B Versatile)
- Vision: Google Gemini 2.0 Flash
- STT: Faster Whisper (distil-small.en, CPU, int8)
- TTS: Kokoro Engine (SSML-based)
- Cache: Redis (DB0 = conversations, DB1 = tool cache)
- Storage: Excel export for health logs

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + TypeScript)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  Voice Chat  │  │ Health Logger│  │ Data Explorer│  │ Map Viewer  │ │
│  │   (Main UI)  │  │  (Metrics)   │  │  (Redis UI)  │  │  (Clinics)  │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
│         │                 │                 │                 │         │
│         └─────────────────┴─────────────────┴─────────────────┘         │
│                                    │                                     │
│                              WebSocket / HTTP                            │
└────────────────────────────────────┼─────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼─────────────────────────────────────┐
│                         BACKEND (FastAPI)                                │
│                                    │                                     │
│  ┌─────────────────────────────────▼──────────────────────────────────┐ │
│  │                      API ROUTES (/api/process)                      │ │
│  │  • Voice Input (audio → Whisper STT)                                │ │
│  │  • Text Input (direct transcript)                                   │ │
│  │  • Image Input (medicine photo → Gemini Vision)                     │ │
│  └─────────────────────────────────┬──────────────────────────────────┘ │
│                                    │                                     │
│  ┌─────────────────────────────────▼──────────────────────────────────┐ │
│  │                    INTENT CLASSIFIER (LLM)                          │ │
│  │  Model: Llama 3.1 8B Instant (fast, lightweight)                   │ │
│  │  Input: User transcript                                             │ │
│  │  Output: { intent, entities }                                       │ │
│  │                                                                      │ │
│  │  Intents:                                                            │ │
│  │    • medicine_info        → Medicine classifier                     │ │
│  │    • medical_news         → News API                                │ │
│  │    • medical_report       → Report generator                        │ │
│  │    • health_monitoring    → Health context Q&A                      │ │
│  │    • nearby_clinic        → Clinic search                           │ │
│  │    • general_conversation → Direct LLM response                     │ │
│  └─────────────────────────────────┬──────────────────────────────────┘ │
│                                    │                                     │
│  ┌─────────────────────────────────▼──────────────────────────────────┐ │
│  │                    MCP ROUTER (Tool Orchestrator)                   │ │
│  │  Routes intent → appropriate tool(s)                                │ │
│  │  Returns: List[ToolOutput]                                          │ │
│  └─────────────────────────────────┬──────────────────────────────────┘ │
│                                    │                                     │
│         ┌──────────────────────────┼──────────────────────────┐         │
│         │                          │                          │         │
│  ┌──────▼──────┐  ┌───────────────▼────────┐  ┌─────────────▼──────┐  │
│  │   TOOL 1    │  │      TOOL 2            │  │     TOOL 3         │  │
│  │  Medicine   │  │   Medical News         │  │  Medical Report    │  │
│  │ Classifier  │  │   (NewsAPI)            │  │   Generator        │  │
│  │  (Gemini)   │  │                        │  │                    │  │
│  │             │  │  Cache: Redis DB1      │  │  Data: Redis DB0   │  │
│  │ Cache: DB1  │  │  TTL: 36 hours         │  │  (history + logs)  │  │
│  │ TTL: 36h    │  └────────────────────────┘  └────────────────────┘  │
│  └─────────────┘                                                        │
│                                                                          │
│  ┌──────────────┐  ┌────────────────────┐  ┌──────────────────────┐   │
│  │   TOOL 4     │  │     TOOL 5         │  │      TOOL 6          │   │
│  │   Health     │  │  Nearby Clinic     │  │  Consolidation       │   │
│  │  Monitoring  │  │   Search (OSM)     │  │    Summary           │   │
│  │              │  │                    │  │                      │   │
│  │ Data: DB0    │  │  GPS-based search  │  │  Context: DB0        │   │
│  │ Excel Export │  │  Returns map data  │  │  Summarizes topics   │   │
│  └──────────────┘  └────────────────────┘  └──────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              RESPONSE AGGREGATOR (Final LLM Call)               │   │
│  │  Model: Llama 3.3 70B Versatile                                 │   │
│  │  Input: Tool outputs + conversation context                     │   │
│  │  Output: Voice-ready plain text response                        │   │
│  │  SSML Tone: Mapped per intent (informative/neutral/structured)  │   │
│  └─────────────────────────────────┬───────────────────────────────┘   │
│                                    │                                     │
│  ┌─────────────────────────────────▼───────────────────────────────┐   │
│  │                    TTS ENGINE (Kokoro)                           │   │
│  │  Converts text → audio with SSML tone control                   │   │
│  │  Output: WAV file (16kHz, mono)                                 │   │
│  └─────────────────────────────────┬───────────────────────────────┘   │
│                                    │                                     │
└────────────────────────────────────┼─────────────────────────────────────┘
                                     │
                              Audio Response
                                     │
┌────────────────────────────────────▼─────────────────────────────────────┐
│                         REDIS CACHE LAYER                                │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────┐ │
│  │  DB0: Conversation Cache     │  │  DB1: Tool Retrieval Cache (CAG) │ │
│  │  TTL: 30 hours (108000s)     │  │  TTL: 36 hours (129600s)         │ │
│  │                              │  │                                  │ │
│  │  Keys:                       │  │  Keys:                           │ │
│  │  • ctx:<session_id>          │  │  • medicine_info:<hash>          │ │
│  │  • health:<session_id>       │  │  • medical_news:<hash>           │ │
│  │  • healthchat:<session_id>   │  │  • medical_info:<hash>           │ │
│  │                              │  │                                  │ │
│  │  Persistence: AOF enabled    │  │  Persistence: AOF enabled        │ │
│  └──────────────────────────────┘  └──────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL APIS & SERVICES                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  OpenFDA API │  │  NewsAPI     │  │ Nominatim    │  │ Groq LLM    │ │
│  │  (Drug Info) │  │ (Med News)   │  │ (OSM Clinics)│  │ (Llama 3.3) │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
│  ┌──────────────┐                                                        │
│  │ Gemini Vision│                                                        │
│  │ (Medicine ID)│                                                        │
│  └──────────────┘                                                        │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Tool Descriptions

### TOOL 1: Medicine Classifier (`medicine_classifier_tool.py`)

**Purpose:** Identifies and classifies medicines using Gemini Vision API (for images) or Gemini text model (for voice/text queries).

**Trigger Conditions:**
- Intent: `medicine_info`
- User asks about a specific medicine by name
- User uploads a medicine photo/package
- Examples: "What is paracetamol?", "Tell me about ibuprofen", "Analyze this medicine photo"

**Input Parameters:**
- `input_mode`: "voice" | "text" | "image"
- `medicine_name`: String (for voice/text mode)
- `image_bytes`: Binary image data (for image mode)
- `redis_db1`: Redis connection for caching
- `gemini_client`: Gemini API client

**Processing Flow:**
1. Check Redis DB1 cache for existing classification (voice/text only)
2. If cache miss, call Gemini API with medicine classifier prompt
3. Extract structured JSON response (medicine name, composition, category, purpose, safety notes)
4. Store result in Redis DB1 with 36-hour TTL (voice/text only)
5. Return ToolOutput with medicine_data field

**Output Structure:**
```json
{
  "medicine_name": "Paracetamol",
  "chemical_composition": "N-(4-hydroxyphenyl)acetamide",
  "drug_category": "Analgesic, Antipyretic",
  "purpose": "Pain relief and fever reduction",
  "basic_safety_notes": "Do not exceed 4g per day. Avoid with alcohol.",
  "disclaimer": "Educational purposes only. Consult a pharmacist.",
  "input_mode": "text"
}
```

**Caching Behavior:**
- Voice/Text: Cached in DB1 with key `medicine_info:<medicine_name_hash>`
- Image: NOT cached (not reproducible by key)
- TTL: 36 hours (129600 seconds)

**Error Handling:**
- Returns fallback data with "Classification failed" message
- Logs error details for debugging
- Always includes disclaimer

---

### TOOL 2: Medical News (`news_tool.py`)

**Purpose:** Fetches latest medical and pharmaceutical news from NewsAPI.

**Trigger Conditions:**
- Intent: `medical_news`
- User asks about recent medical developments
- Examples: "Latest news on cancer treatment", "Recent medical news about diabetes", "What's new in cardiology?"

**Input Parameters:**
- `entities`: Dict containing disease/drug keywords
- `redis_db1`: Redis connection for caching

**Processing Flow:**
1. Extract topic from entities (disease, drug, or default to "medical health")
2. Check Redis DB1 cache for recent news on this topic
3. If cache miss, call NewsAPI with:
   - Query: extracted topic
   - Language: English
   - Date range: Last 180 days
   - Sort by: publishedAt (most recent first)
   - Limit: 3 articles
4. Parse and structure article data
5. Store in Redis DB1 with 36-hour TTL
6. Return ToolOutput with article list

**Output Structure:**
```json
{
  "topic": "cancer treatment",
  "articles": [
    {
      "title": "New Breakthrough in Cancer Immunotherapy",
      "description": "Researchers discover...",
      "url": "https://...",
      "published_at": "2026-03-04T10:30:00Z"
    }
  ],
  "source": "NewsAPI"
}
```

**Caching Behavior:**
- Cached in DB1 with key `medical_news:<topic_hash>`
- TTL: 36 hours (129600 seconds)
- Prevents redundant API calls for same topic

**Error Handling:**
- Returns message: "Unable to fetch news for '{topic}' at this time"
- Logs API errors
- Graceful degradation

---

### TOOL 3: Medical Report Generator (`report_tool.py`)

**Purpose:** Generates a comprehensive medical report summarizing user's conversation history and health logs.

**Trigger Conditions:**
- Intent: `medical_report`
- User requests a summary of their health data
- Examples: "Generate my medical report", "Show me my health summary", "What have we discussed?"

**Input Parameters:**
- `session_id`: User session identifier
- `redis_db0`: Redis connection for conversation/health data

**Processing Flow:**
1. Retrieve conversation history from Redis DB0 (`ctx:<session_id>`)
2. Retrieve health logs from Redis DB0 (`health:<session_id>`)
3. Extract user queries (last 15 interactions)
4. Summarize latest health metrics (BP, sugar, weight, mood, symptoms)
5. Build structured report with timestamps
6. Return ToolOutput with report_data field

**Output Structure:**
```json
{
  "session_id": "abc123",
  "generated_at": "2026-03-05T14:30:00Z",
  "total_interactions": 25,
  "topics_discussed": [
    "What is aspirin used for?",
    "Tell me about diabetes management"
  ],
  "health_metrics": {
    "total_entries": 10,
    "condition": "diabetes",
    "latest_systolic_bp": 125,
    "latest_diastolic_bp": 82,
    "latest_fasting_sugar": 110,
    "latest_postmeal_sugar": 145,
    "latest_weight_kg": 72.5,
    "mood": "good",
    "symptoms": ["mild headache"],
    "notes": "Feeling better today"
  },
  "has_health_data": true,
  "has_conversation_data": true,
  "disclaimer": "This is not medical advice..."
}
```

**Data Sources:**
- Conversation history: `ctx:<session_id>` (DB0)
- Health logs: `health:<session_id>` (DB0)

**No Caching:** Report is generated fresh each time to reflect latest data.

---

### TOOL 4: Health Monitor (`health_monitor_tool.py`)

**Purpose:** Tracks user health metrics, performs threshold analysis, and provides personalized health recommendations with daily checklist.

**Trigger Conditions:**
- Intent: `health_monitoring`
- User asks health-metric-specific questions
- Examples: "How is my blood pressure?", "Show my health trends", "Am I improving?"

**Input Parameters:**
- `session_id`: User session identifier
- `redis_db0`: Redis connection for health logs
- `llm_client`: LLM client for trend analysis

**Processing Flow:**
1. Retrieve last 30 health log entries from Redis DB0
2. Run threshold checks on BP and sugar levels
3. Flag dangerous/warning readings
4. Call LLM with health analysis prompt
5. Generate structured analysis with:
   - Summary of health trends
   - Flagged readings (high BP, high sugar)
   - Diet suggestions
   - Lifestyle recommendations
   - Mental health guidance
   - Daily checklist
6. Return ToolOutput with analysis

**Health Thresholds:**
```python
THRESHOLDS = {
    "systolic_bp": [
        {"level": "danger", "min": 140},
        {"level": "warning", "min": 120}
    ],
    "diastolic_bp": [
        {"level": "danger", "min": 90},
        {"level": "warning", "min": 80}
    ],
    "sugar_fasting": [
        {"level": "danger", "min": 126},
        {"level": "warning", "min": 100}
    ],
    "sugar_postmeal": [
        {"level": "danger", "min": 200},
        {"level": "warning", "min": 140}
    ]
}
```

**Output Structure:**
```json
{
  "summary": "Your blood pressure has been stable...",
  "flagged_readings": [
    {
      "timestamp": "2026-03-05T08:00:00Z",
      "field": "systolic_bp",
      "value": 145,
      "level": "danger",
      "note": "Systolic BP = 145 exceeds danger threshold (140)"
    }
  ],
  "diet_suggestions": [
    "Reduce sodium intake to less than 2300mg per day",
    "Increase potassium-rich foods like bananas and spinach"
  ],
  "lifestyle_recommendations": [
    "Aim for 30 minutes of moderate exercise daily",
    "Practice stress-reduction techniques like meditation"
  ],
  "mental_health_guidance": "Consider mindfulness exercises...",
  "daily_checklist": [
    "Log your daily health readings",
    "Take medications on time",
    "Drink 8 glasses of water",
    "Get 7-8 hours of sleep",
    "Do 30 minutes of light exercise"
  ],
  "disclaimer": "This is general health information only..."
}
```

**Health Log Entry Function:**
- Logs are stored in Redis DB0 with key `health:<session_id>`
- TTL: 30 hours (108000 seconds)
- Also exported to Excel: `health_data/health_<session_id>.xlsx`

**Excel Export:**
- Columns: timestamp, condition, systolic_bp, diastolic_bp, sugar_fasting, sugar_postmeal, weight_kg, mood, symptoms, notes
- Persistent storage for long-term tracking
- Automatic workbook creation if not exists

---

### TOOL 5: Nearby Clinic Search (`nearby_clinic_tool.py`)

**Purpose:** Finds nearest clinics and hospitals using OpenStreetMap Nominatim API with GPS precision.

**Trigger Conditions:**
- Intent: `nearby_clinic`
- User requests medical facility locations
- Examples: "Find nearby clinics", "Where is the nearest hospital?", "I need immediate medical help"

**Input Parameters:**
- `entities`: Dict containing location data
  - `lat`: GPS latitude (optional, from browser geolocation)
  - `lng`: GPS longitude (optional, from browser geolocation)
  - `location`: Location name (fallback if no GPS)

**Processing Flow:**
1. Check if exact GPS coordinates provided (lat/lng)
2. If GPS available: Use coordinates directly (maximum precision)
3. If no GPS: Geocode location name to coordinates
4. Search Nominatim for hospitals and clinics near coordinates
5. Return top 10 results with name, address, lat, lng
6. Build map_data structure for frontend map display

**Output Structure:**
```json
{
  "location": "Coimbatore",
  "clinics": [
    {
      "name": "City General Hospital",
      "address": "123 Main St, Coimbatore, Tamil Nadu",
      "lat": 11.0168,
      "lng": 76.9558
    }
  ],
  "count": 10
}
```

**Map Data Structure:**
```json
{
  "type": "clinics",
  "search_location": "Coimbatore",
  "center_lat": 11.0168,
  "center_lng": 76.9558,
  "locations": [...]
}
```

**GPS Precision:**
- Browser geolocation provides exact coordinates
- Skips geocoding step for faster, more accurate results
- Fallback to location name if GPS unavailable

**No Caching:** Real-time search for current location data.

---

### TOOL 6: Consolidation Summary (`consolidation_tool.py`)

**Purpose:** Retrieves and summarizes conversation history for the user.

**Trigger Conditions:**
- Implicit: Used when user asks to summarize past discussions
- Examples: "What have we talked about?", "Summarize our conversation"

**Input Parameters:**
- `entities`: Dict (not heavily used)
- `redis_db0`: Redis connection for conversation history
- `session_id`: User session identifier

**Processing Flow:**
1. Retrieve full conversation history from Redis DB0
2. Extract user messages (role="user")
3. Truncate each message to 120 characters
4. Return last 10 user queries
5. LLM aggregator formats into natural summary

**Output Structure:**
```json
{
  "session_id": "abc123",
  "total_turns": 25,
  "topics_discussed": [
    "What is aspirin used for?",
    "Tell me about diabetes management",
    "Find nearby clinics"
  ],
  "summary_request": "Please consolidate and summarize these topics for the user."
}
```

**Data Source:**
- Conversation history: `ctx:<session_id>` (DB0)

**No Caching:** Always retrieves fresh conversation data.

---

### DEPRECATED: Medicine Availability Tool

**Status:** REMOVED in v2.0

**Replacement:** `medicine_classifier_tool.py`

**Reason:** New tool provides better classification with Gemini Vision, does not recommend dosages or prescribe medicines (safety compliance).

---

## System Prompts

### 1. Intent Classification Prompt

**Model:** Llama 3.1 8B Instant (fast, lightweight)  
**Purpose:** Classify user intent and extract entities  
**Max Tokens:** 128

```
You are Dr. Elena, a medical intent classifier for a voice-based healthcare assistant.

Your task: Analyze the user's input and classify it into ONE of these intents:

1. medicine_info — User asks about a specific medicine (name, usage, side effects, composition)
2. medical_news — User wants latest medical or pharmaceutical news
3. medical_report — User requests a summary of their stored health data
4. health_monitoring — User asks about their health metrics (BP, sugar, trends, analysis)
5. nearby_clinic — User needs to find nearby clinics or hospitals
6. general_conversation — General health questions, greetings, chitchat

Extract entities when relevant:
- drug: medicine name
- disease: condition name
- location: place name for clinic search
- lat/lng: GPS coordinates (if provided)

Return ONLY valid JSON:
{
  "intent": "<one of the 6 intents above>",
  "entities": {
    "drug": "...",
    "disease": "...",
    "location": "..."
  }
}

Examples:
User: "What is paracetamol used for?"
Response: {"intent": "medicine_info", "entities": {"drug": "paracetamol"}}

User: "Latest news on cancer treatment"
Response: {"intent": "medical_news", "entities": {"disease": "cancer"}}

User: "Show me my health summary"
Response: {"intent": "medical_report", "entities": {}}

User: "How is my blood pressure?"
Response: {"intent": "health_monitoring", "entities": {}}

User: "Find nearby clinics"
Response: {"intent": "nearby_clinic", "entities": {"location": "nearby"}}

User: "Hello, how are you?"
Response: {"intent": "general_conversation", "entities": {}}

Now classify this input:
```

---

### 2. Medicine Classifier Prompt (Gemini Vision)

**Model:** Gemini 2.0 Flash  
**Purpose:** Classify medicine from text or image  
**Used by:** `medicine_classifier_tool.py`

```
You are Dr. Elena, a pharmaceutical information specialist.

Analyze the provided medicine (name or image) and return structured information in JSON format.

Required fields:
- medicine_name: Official or common name
- chemical_composition: Active ingredients
- drug_category: Classification (e.g., Analgesic, Antibiotic, Antihypertensive)
- purpose: Primary medical uses (2-3 sentences)
- basic_safety_notes: Key safety information (contraindications, warnings)

IMPORTANT RULES:
1. Do NOT provide dosage amounts or administration instructions
2. Do NOT prescribe or recommend medicines
3. This is educational information only
4. Always emphasize consulting a healthcare professional

Return ONLY valid JSON:
{
  "medicine_name": "...",
  "chemical_composition": "...",
  "drug_category": "...",
  "purpose": "...",
  "basic_safety_notes": "..."
}

If you cannot identify the medicine, return:
{
  "medicine_name": "Unknown",
  "chemical_composition": "Unable to identify",
  "drug_category": "Unknown",
  "purpose": "Unable to classify",
  "basic_safety_notes": "Please consult a pharmacist for identification."
}
```

---

### 3. Response Aggregation Prompt

**Model:** Llama 3.3 70B Versatile  
**Purpose:** Combine tool outputs into final response  
**Max Tokens:** 300

```
You are Dr. Elena, a compassionate AI health assistant.

Your role: Synthesize tool outputs and conversation context into a clear, voice-friendly response.

Guidelines:
1. Be warm, empathetic, and professional
2. Use simple language suitable for voice delivery
3. Prioritize safety — always recommend consulting healthcare professionals
4. Keep responses concise (2-3 sentences for simple queries, 4-5 for complex)
5. Do NOT use markdown, bullet points, or special formatting
6. Speak naturally as if having a conversation
7. Include disclaimers when discussing medical information
8. If tool data is missing or incomplete, acknowledge limitations gracefully

Response style:
- Medicine info: Educational, clear, emphasize consulting pharmacist
- Medical news: Informative, neutral tone, cite source
- Health monitoring: Supportive, actionable, encouraging
- Medical report: Structured, comprehensive, reassuring
- Clinic search: Helpful, urgent if needed, provide clear directions
- General conversation: Friendly, warm, conversational

CRITICAL: Never provide medical diagnoses, prescribe medications, or give specific dosage instructions.

Now synthesize this information into a natural voice response:
```

---

### 4. General Conversation Prompt

**Model:** Llama 3.3 70B Versatile  
**Purpose:** Handle general health Q&A and chitchat  
**Max Tokens:** 300

```
You are Dr. Elena, a friendly AI health assistant.

You provide general health information, answer wellness questions, and engage in supportive conversation.

Your personality:
- Warm, empathetic, and approachable
- Professional but not clinical
- Encouraging and positive
- Patient and understanding

Guidelines:
1. Provide evidence-based general health information
2. Use simple, conversational language
3. Be supportive and non-judgmental
4. Always recommend consulting healthcare professionals for specific medical concerns
5. Keep responses concise and voice-friendly (2-4 sentences)
6. Do NOT diagnose conditions or prescribe treatments
7. Do NOT provide specific medical advice
8. Acknowledge when questions are outside your scope

Topics you can discuss:
- General wellness and healthy lifestyle
- Basic health concepts and terminology
- When to seek medical attention
- Emotional support and encouragement
- Health-related questions and concerns

Topics to redirect to professionals:
- Specific diagnoses
- Treatment plans
- Medication dosages
- Emergency medical situations
- Mental health crises

Now respond to the user's message:
```

---

### 5. Health Analysis Prompt

**Model:** Llama 3.3 70B Versatile  
**Purpose:** Analyze health trends and provide recommendations  
**Max Tokens:** 600  
**Used by:** `health_monitor_tool.py`

```
You are Dr. Elena, a health monitoring specialist.

Analyze the provided health log data and generate a comprehensive health analysis.

Input data includes:
- Blood pressure readings (systolic/diastolic)
- Blood sugar levels (fasting/postmeal)
- Weight measurements
- Mood tracking
- Symptoms
- Pre-flagged readings that exceed safe thresholds

Your task: Generate a structured JSON response with:

1. summary: Overall health trend analysis (3-4 sentences)
2. flagged_readings: List of concerning readings with explanations
3. diet_suggestions: 3-5 specific dietary recommendations
4. lifestyle_recommendations: 3-5 actionable lifestyle changes
5. mental_health_guidance: Brief mental wellness advice (2-3 sentences)
6. daily_checklist: 5-7 daily health tasks for the user

Guidelines:
- Be encouraging and supportive, not alarmist
- Provide specific, actionable recommendations
- Acknowledge improvements and positive trends
- For concerning readings, recommend consulting a doctor
- Tailor advice to the user's specific condition (diabetes, hypertension, etc.)
- Daily checklist should be realistic and achievable

Return ONLY valid JSON:
{
  "summary": "...",
  "flagged_readings": [
    {
      "timestamp": "...",
      "field": "systolic_bp",
      "value": 145,
      "level": "danger",
      "note": "..."
    }
  ],
  "diet_suggestions": ["...", "..."],
  "lifestyle_recommendations": ["...", "..."],
  "mental_health_guidance": "...",
  "daily_checklist": ["...", "...", "..."]
}

Now analyze this health data:
```

---

### 6. Medical Report Generation Prompt

**Model:** Llama 3.3 70B Versatile  
**Purpose:** Format medical report data into voice-friendly summary  
**Max Tokens:** 300  
**Used by:** Response aggregator when intent = medical_report

```
You are Dr. Elena, generating a personalized health summary report.

You have access to:
- User's conversation history (topics discussed)
- Health log entries (BP, sugar, weight, mood, symptoms)
- Total interaction count
- Latest health metrics

Your task: Create a warm, comprehensive summary that:
1. Acknowledges the user's engagement with their health
2. Summarizes key topics discussed
3. Highlights important health metrics
4. Notes any trends or patterns
5. Encourages continued health monitoring
6. Reminds user this is for personal awareness, not medical advice

Style:
- Conversational and supportive
- Organized but not overly formal
- Voice-friendly (no bullet points or markdown)
- 4-6 sentences total

Example structure:
"Based on our conversations, we've discussed [topics]. Your health logs show [metrics summary]. I've noticed [trend or pattern]. Keep up the great work with [positive behavior], and remember to [recommendation]. This summary is for your personal awareness — always consult your healthcare provider for medical decisions."

Now generate the report summary:
```

---

## Data Flow

### Complete Request Flow (Voice Input Example)

```
1. USER SPEAKS
   ↓
2. FRONTEND: Capture audio → Send to /api/process
   ↓
3. BACKEND: Whisper STT → Transcript
   ↓
4. INTENT CLASSIFIER (Llama 3.1 8B)
   Input: "What is paracetamol used for?"
   Output: {intent: "medicine_info", entities: {drug: "paracetamol"}}
   ↓
5. MCP ROUTER
   Routes to: medicine_classifier_tool
   ↓
6. MEDICINE CLASSIFIER TOOL
   a. Check Redis DB1 cache: medicine_info:paracetamol
   b. Cache MISS → Call Gemini API
   c. Gemini returns structured medicine data
   d. Store in Redis DB1 (TTL: 36h)
   e. Return ToolOutput
   ↓
7. RESPONSE AGGREGATOR (Llama 3.3 70B)
   Input: Tool output + conversation context
   Output: "Paracetamol is a pain reliever and fever reducer..."
   ↓
8. TTS ENGINE (Kokoro)
   Input: Text response + SSML tone (informative)
   Output: WAV audio file
   ↓
9. BACKEND: Save audio → Return response JSON
   {
     "response_text": "...",
     "audio_url": "/static/audio/abc123.wav",
     "medicine_data": {...},
     "session_id": "abc123"
   }
   ↓
10. FRONTEND: Play audio + Display medicine card
    ↓
11. REDIS DB0: Store conversation turn
    ctx:abc123 → [
      {role: "user", content: "What is paracetamol used for?"},
      {role: "assistant", content: "Paracetamol is a pain reliever..."}
    ]
```

### Cache Hit Flow (Faster Response)

```
1. USER: "What is paracetamol used for?" (again)
   ↓
2. Intent Classifier → medicine_info
   ↓
3. Medicine Classifier Tool
   a. Check Redis DB1: medicine_info:paracetamol
   b. Cache HIT! ✓
   c. Return cached data (no Gemini API call)
   ↓
4. Response Aggregator → TTS → Frontend
   (Same as above, but 2-3 seconds faster)
```

---

## Redis Database Structure

### DB0: Conversation Cache (TTL: 30 hours)

**Purpose:** Store conversation history and health logs for context-aware responses.

**Key Patterns:**

1. **Conversation History**
   ```
   Key: ctx:<session_id>
   Type: String (JSON array)
   TTL: 108000 seconds (30 hours)
   Value: [
     {"role": "user", "content": "What is aspirin?"},
     {"role": "assistant", "content": "Aspirin is a pain reliever..."}
   ]
   ```

2. **Health Logs**
   ```
   Key: health:<session_id>
   Type: String (JSON array)
   TTL: 108000 seconds (30 hours)
   Value: [
     {
       "timestamp": "2026-03-05T08:00:00Z",
       "condition": "diabetes",
       "systolic_bp": 125,
       "diastolic_bp": 82,
       "sugar_fasting": 110,
       "sugar_postmeal": 145,
       "weight_kg": 72.5,
       "mood": "good",
       "symptoms": ["mild headache"],
       "notes": "Feeling better today"
     }
   ]
   ```

3. **Health Chat History**
   ```
   Key: healthchat:<session_id>
   Type: String (JSON array)
   TTL: 108000 seconds (30 hours)
   Value: [
     {"role": "user", "content": "How is my BP?"},
     {"role": "assistant", "content": "Your latest BP reading..."}
   ]
   ```

**Persistence:** AOF (Append-Only File) enabled for durability.

---

### DB1: Tool Retrieval Cache (TTL: 36 hours)

**Purpose:** Cache-Augmented Generation (CAG) — store tool outputs to reduce API calls and improve response time.

**Key Patterns:**

1. **Medicine Information**
   ```
   Key: medicine_info:<medicine_name_hash>
   Type: String (JSON object)
   TTL: 129600 seconds (36 hours)
   Value: {
     "medicine_name": "Paracetamol",
     "chemical_composition": "...",
     "drug_category": "Analgesic",
     "purpose": "...",
     "basic_safety_notes": "..."
   }
   ```

2. **Medical News**
   ```
   Key: medical_news:<topic_hash>
   Type: String (JSON object)
   TTL: 129600 seconds (36 hours)
   Value: {
     "topic": "cancer treatment",
     "articles": [...],
     "source": "NewsAPI"
   }
   ```

3. **Medical API Data (OpenFDA)**
   ```
   Key: medical_info:<query_hash>
   Type: String (JSON object)
   TTL: 129600 seconds (36 hours)
   Value: {
     "description": "...",
     "indications": "...",
     "warnings": "...",
     "source": "OpenFDA",
     "query": "metformin"
   }
   ```

**Persistence:** AOF (Append-Only File) enabled for durability.

**Cache Key Generation:**
```python
def build_cache_key(tool_name: str, query: str) -> str:
    """Generate deterministic cache key."""
    import hashlib
    query_hash = hashlib.sha256(query.lower().encode()).hexdigest()[:16]
    return f"{tool_name}:{query_hash}"
```

---

## Intent Classification

### Intent Types and Examples

| Intent | Description | Example Queries | Tool Routed |
|--------|-------------|-----------------|-------------|
| `medicine_info` | Medicine identification and classification | "What is paracetamol?", "Tell me about ibuprofen", "Analyze this medicine photo" | medicine_classifier_tool |
| `medical_news` | Latest medical/pharmaceutical news | "Latest news on cancer", "Recent diabetes research", "Medical breakthroughs" | news_tool |
| `medical_report` | Generate health summary report | "Show my health summary", "Generate my report", "What have we discussed?" | report_tool |
| `health_monitoring` | Health metrics Q&A | "How is my blood pressure?", "Show my health trends", "Am I improving?" | health_monitor_tool |
| `nearby_clinic` | Find medical facilities | "Find nearby clinics", "Where is the nearest hospital?", "I need immediate help" | nearby_clinic_tool |
| `general_conversation` | General health Q&A, greetings | "Hello", "How are you?", "What is diabetes?", "Tips for better sleep" | No tool (direct LLM) |

### Entity Extraction

**Entities extracted by intent classifier:**

- `drug`: Medicine name (for medicine_info, medical_news)
- `disease`: Condition name (for medical_news, medical_info)
- `location`: Place name (for nearby_clinic)
- `lat`: GPS latitude (for nearby_clinic, from browser geolocation)
- `lng`: GPS longitude (for nearby_clinic, from browser geolocation)

**Example:**
```json
{
  "intent": "nearby_clinic",
  "entities": {
    "location": "Coimbatore",
    "lat": 11.0168,
    "lng": 76.9558
  }
}
```

---

## Response Aggregation

### SSML Tone Mapping

**Purpose:** Control TTS voice characteristics based on intent type.

| Intent | SSML Tone | Voice Characteristics |
|--------|-----------|----------------------|
| `medicine_info` | `informative` | Clear, educational, slightly slower |
| `medical_news` | `neutral` | News broadcast style, steady pace |
| `medical_report` | `structured` | Deliberate, organized, professional |
| `health_monitoring` | `informative` | Supportive, encouraging, clear |
| `general_conversation` | `neutral` | Natural, conversational, warm |

### Aggregation Process

1. **Collect Inputs:**
   - Tool outputs (List[ToolOutput])
   - Intent result (intent + entities)
   - Conversation context (last 3 turns from DB0)

2. **Build Context String:**
   ```
   User query: [transcript]
   
   Tool data:
   [medicine_info]: {"medicine_name": "...", ...}
   
   Recent conversation:
   User: What is aspirin?
   Assistant: Aspirin is a pain reliever...
   ```

3. **Select System Prompt:**
   - If intent = "general_conversation" → GENERAL_CONVERSATION_PROMPT
   - Else → AGGREGATION_PROMPT

4. **LLM Call:**
   - Model: Llama 3.3 70B Versatile
   - Max tokens: 300
   - Temperature: 0.3

5. **Post-Processing:**
   - Strip markdown formatting
   - Truncate to 600 characters max
   - Return plain text for TTS

6. **TTS Generation:**
   - Apply SSML tone based on intent
   - Generate WAV audio (16kHz, mono)
   - Save to static/audio/

---

## Test Questions for DB1 Cache Population

### Medicine Info (Tool 1)
```
1. "What is paracetamol?"
2. "Tell me about ibuprofen"
3. "What is aspirin used for?"
4. "Explain metformin"
5. "What is amoxicillin?"
6. "Tell me about lisinopril"
7. "What is atorvastatin?"
8. "Explain omeprazole"
```

### Medical News (Tool 2)
```
1. "Latest news on cancer treatment"
2. "Recent medical news about diabetes"
3. "What's new in cardiology?"
4. "Latest research on Alzheimer's"
5. "Recent breakthroughs in immunotherapy"
6. "News about COVID-19 treatments"
7. "Latest developments in gene therapy"
8. "Recent pharmaceutical discoveries"
```

### Medical API (OpenFDA)
```
1. "Side effects of metformin"
2. "What are the warnings for aspirin?"
3. "Tell me about lisinopril indications"
4. "Warfarin drug information"
5. "Insulin usage information"
```

### Health Monitoring (Tool 4)
```
1. "Show me my health summary"
2. "How is my blood pressure?"
3. "Analyze my health trends"
4. "Am I improving?"
5. "What are my flagged readings?"
```

### Medical Report (Tool 3)
```
1. "Generate my medical report"
2. "Show my health summary"
3. "What have we discussed?"
4. "Summarize my health data"
```

### Nearby Clinic (Tool 5)
```
1. "Find nearby clinics"
2. "Where is the nearest hospital?"
3. "I need immediate medical help"
4. "Show me clinics in Coimbatore"
```

---

## Configuration

### Environment Variables (.env)

```bash
# LLM Configuration
GROQ_API_KEY=your_groq_api_key
LLM_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=512
LLM_TIMEOUT=30

# Gemini Vision
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB0=0
REDIS_DB1=1

# TTL Settings (seconds)
CONTEXT_TTL_SECONDS=108000      # 30 hours (DB0 conversations)
HEALTH_LOG_TTL_SECONDS=108000   # 30 hours (DB0 health logs)
TTL_DRUG=129600                 # 36 hours (DB1 OpenFDA cache)
TTL_NEWS=129600                 # 36 hours (DB1 NewsAPI cache)
TTL_MEDICINE=129600             # 36 hours (DB1 Gemini medicine cache)

# Whisper STT
WHISPER_MODEL_SIZE=distil-whisper/distil-small.en
WHISPER_DEVICE=cpu

# External APIs
MEDICAL_API_BASE_URL=https://api.fda.gov/drug
NEWS_API_KEY=your_newsapi_key
MAPS_API_KEY=your_maps_api_key
DEFAULT_LOCATION=Coimbatore

# Server
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
STATIC_AUDIO_DIR=static/audio
HEALTH_EXCEL_DIR=health_data
```

### Redis Configuration (redis.conf)

```conf
# Persistence
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# Memory Management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Database Count
databases 16

# Logging
loglevel notice
logfile ""
```

---

## Performance Metrics

### Response Times (Typical)

| Scenario | Time | Notes |
|----------|------|-------|
| Cache HIT (medicine info) | 1-2s | Redis retrieval + LLM aggregation + TTS |
| Cache MISS (medicine info) | 3-5s | Gemini API call + caching + aggregation + TTS |
| Medical news (cache HIT) | 1-2s | Redis retrieval + aggregation + TTS |
| Medical news (cache MISS) | 4-6s | NewsAPI call + caching + aggregation + TTS |
| Health analysis | 3-4s | DB0 retrieval + LLM analysis + TTS |
| Medical report | 2-3s | DB0 retrieval + formatting + TTS |
| Nearby clinic search | 3-5s | Nominatim API + map data + TTS |
| General conversation | 2-3s | LLM call + TTS |

### Cache Hit Rates (Expected)

- Medicine info: 70-80% (common medicines queried repeatedly)
- Medical news: 60-70% (same topics within 36h window)
- OpenFDA data: 65-75% (common drugs)

### API Call Reduction

- Without cache: ~100% API calls
- With cache (36h TTL): ~25-30% API calls
- Cost savings: ~70-75%

---

## Security & Compliance

### Medical Disclaimer

All responses include appropriate disclaimers:
- "This is for educational purposes only"
- "Consult a licensed healthcare provider"
- "Not medical advice, diagnosis, or treatment"

### Data Privacy

- Session IDs are UUIDs (not personally identifiable)
- No PII stored in Redis
- Health logs stored locally (Excel) with session ID only
- No data shared with third parties

### Safety Measures

1. **No Prescriptions:** System never prescribes medications or dosages
2. **No Diagnoses:** System never diagnoses medical conditions
3. **Professional Referral:** Always recommends consulting healthcare providers
4. **Threshold Alerts:** Flags dangerous health readings
5. **Emergency Guidance:** Directs users to emergency services when needed

---

## Future Enhancements

1. **Multi-language Support:** Translate prompts and responses
2. **Voice Biometrics:** User identification via voice
3. **Medication Reminders:** Push notifications for medication schedules
4. **Telemedicine Integration:** Connect to video consultation services
5. **Wearable Integration:** Sync with fitness trackers and smartwatches
6. **Advanced Analytics:** ML-based health trend prediction
7. **Family Accounts:** Multi-user support with role-based access
8. **Prescription OCR:** Extract medication info from prescription images
9. **Symptom Checker:** Interactive symptom assessment tool
10. **Health Goals:** Set and track personalized health objectives

---

## Troubleshooting

### Common Issues

**1. Redis Connection Failed**
- Check Redis server is running: `redis-cli ping`
- Verify host/port in .env file
- Check firewall settings

**2. Whisper Model Loading Error**
- Ensure model downloaded: `distil-whisper/distil-small.en`
- Check disk space for model files
- Verify Python environment has `faster-whisper` installed

**3. Gemini API Error**
- Verify API key is valid
- Check API quota/rate limits
- Ensure internet connectivity

**4. TTS Audio Not Playing**
- Check static/audio directory exists and is writable
- Verify audio file was created
- Check browser console for CORS errors

**5. Cache Not Working**
- Verify Redis DB1 is accessible
- Check TTL settings in config
- Use `redis-cli` to inspect keys manually

---

## Conclusion

This Voice AI Healthcare Assistant provides a comprehensive, production-ready solution for voice-based health information and monitoring. The architecture emphasizes:

- **Performance:** Cache-Augmented Generation reduces API calls by 70%
- **Accuracy:** Gemini Vision for medicine identification
- **Context:** Redis-based conversation memory
- **Safety:** Medical disclaimers and professional referrals
- **Scalability:** Modular tool architecture
- **User Experience:** Natural voice interaction with SSML tone control

For questions or support, refer to the README.md or contact the development team.

---

**Document Version:** 1.0  
**Last Updated:** March 5, 2026  
**System Version:** 3.0.0
