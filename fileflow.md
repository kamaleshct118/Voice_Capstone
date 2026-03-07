# Voice-First Healthcare Assistant: File Execution Flow

This document maps out the backend execution pipeline of the Voice Medical Assistant. It follows a user's request from the moment the audio arrives at the server to the moment the synthesized voice response is returned, detailing exactly **what** each file does and **why**.

---

## The Core Pipeline Flow

### 1. Ingestion & Validation
When the user speaks into the frontend, the browser sends an audio payload (or text payload) to the backend.

*   **`backend/app/api/routes.py` (The Orchestrator)**
    *   **What it does:** The main entry point. Specifically, the `POST /api/process` endpoint. It receives the multipart form data (audio, session ID, GPS coordinates).
    *   **Why:** It acts as the "boss" of the pipeline, delegating tasks to other modules step-by-step and collecting the results.

*   **`backend/app/utils/validators.py`**
    *   **What it does:** Reads the raw uploaded audio or image file, checks file sizes, and extracts the raw bytes.
    *   **Why:** For security and integrity, ensuring the system doesn't process corrupt or oversized malicious files.

### 2. Voice to Text (STT)
The system must convert the raw audio bytes into understandable text.

*   **`backend/app/voice/vad.py` (Voice Activity Detection)**
    *   **What it does:** Takes the audio bytes, converts them into a numpy array, and trims out background noise and silence from the beginning and end.
    *   **Why:** Fast-forwards past silence so the STT engine has less total audio to process, significantly reducing latency and preventing hallucinations from background noise.

*   **`backend/app/voice/stt.py` (Automatic Speech Recognition)**
    *   **What it does:** Feeds the cleaned audio array into the local `faster-whisper` model to generate a text transcript.
    *   **Why:** The LLM cannot "understand" raw audio files directly; it needs a plain text string representation of the user's speech.

*   **`backend/app/voice/tone_analysis.py`**
    *   **What it does:** Performs a lightweight analysis on the transcript to guess the user's emotional state (e.g., panicked, neutral).
    *   **Why:** Provides supplementary metadata that can be used down the line to adjust responses if the user seems in distress.

### 3. Understanding the User (Intent Classification)
Before answering, the system must definitively categorize *what* the user is trying to accomplish.

*   **`backend/app/mcp/intent_classifier.py`**
    *   **What it does:** Connects to the LLM Client, passing the user's transcript to determine the intent category.
    *   **Why:** We enforce a strict tool-calling architecture. By figuring out the intent first, we avoid chaotic guessing and immediately route to the precise database or tool needed.

*   **`backend/app/llm/prompts.py` (The Rulebook)**
    *   **What it does:** Contains the `INTENT_CLASSIFICATION_PROMPT` which instructs the LLM on how to classify the intent (e.g., `medicine_info`, `health_monitoring`, `general_conversation`) and how to extract entities.
    *   **Why:** Centralizes all "rules" for the LLM so it behaves predictably and consistently across requests.

### 4. Fetching Data (Tool Routing)
Based on the identified intent, the system executes specialized tools.

*   **`backend/app/mcp/router.py`**
    *   **What it does:** A switchboard. If the intent is `medicine_info`, it fires the medicine tool. If it's `nearby_clinic`, it triggers the map tool. 
    *   **Why:** Decouples the intent logic from the actual data-fetching logic, so you can add new tools without breaking the core pipeline.

*   **`backend/app/tools/*.py` (e.g., `medicine_classifier_tool.py`, `health_monitor_tool.py`)**
    *   **What they do:** The actual "workers". They might query Google Gemini for image analysis, hit PostgreSQL for health logs, or query the Overpass API for nearby hospitals.
    *   **Why:** They gather factual, external data that the LLM wouldn't know otherwise, preventing AI hallucinations.

### 5. Remembering the Context (Short-Term Memory)
The assistant must remember what was said 10 seconds ago.

*   **`backend/app/cache/db0_context.py`**
    *   **What it does:** Saves the user's transcript into Redis DB0 under their `session_id`. If the conversation exceeds 10 messages, it triggers the LLM to compress the history into a single summary paragraph.
    *   **Why:** Maintains contextual memory so real-time follow-up questions work smoothly, while compression prevents the system from crashing due to immense token overload on long sessions.

### 6. Writing the Response (Aggregation)
The system has the user's question, the conversation history, and the raw tool data. Now it must compose a spoken reply.

*   **`backend/app/mcp/response_aggregator.py`**
    *   **What it does:** 
        1. Takes the history, user query, and raw data dumps, and runs them through the LLM (`AGGREGATION_PROMPT`) to generate a clean, empathetic, plain-English response. 
        2. Contains the `_TONE_MAP` dictionary (e.g., `"medical_report": "structured"`) to figure out what voice style should be used.
    *   **Why:** You don't want the TTS engine reading raw JSON data aloud to a patient. This step transforms data into an empathetic, human-like spoken narrative.

### 7. Formatting for Voice (SSML)
The TTS engine needs XML instructions to know *how* to speak the generated text.

*   **`backend/app/voice/ssml_builder.py`**
    *   **What it does:** Wraps the plain-text response from Step 6 in `<speak>` and `<prosody>` XML tags based on the assigned tone. It adjusts the `rate` (speed), `pitch`, and adds `<break>` tags for dramatic or deliberate pauses.
    *   **Why:** Ensures the voice acts realistically. A medical report reads slowly and deliberately, while a general greeting is spoken cheerfully and briskly.

### 8. Voice Synthesis & Delivery
The final step in the backend process.

*   **`backend/app/api/routes.py` (via `_save_audio_file`)**
    *   **What it does:** Passes the final SSML payload to the Kokoro TTS engine. Kokoro generates a `.wav` file saved to disk (`/static/audio/`). The route then sends the URL of this audio file back to the React frontend as a JSON response.
    *   **Why:** Bridges the gap between the backend python execution and the user's web browser, returning the final audio payload that plays back on their device.

---

## High-Level Visual Summary

```text
[User Speaks 🎤]
       │
       ▼
routes.py (Receives Audio)
       │
       ▼
vad.py & stt.py (Trims noise & Translates to Text)
       │
       ▼
intent_classifier.py (Uses prompts.py to find Intent like "medicine_info")
       │
       ▼
mcp/router.py (Triggers the specific tool: e.g., medicine_classifier_tool.py)
       │
       ▼
db0_context.py (Saves user text to Redis memory)
       │
       ▼
response_aggregator.py (Writes friendly text using tool data AND picks SSML tone)
       │
       ▼
db0_context.py (Saves Assistant text to Redis memory)
       │
       ▼
ssml_builder.py (Wraps text in XML tags for Pitch/Rate/Pauses)
       │
       ▼
routes.py (Calls Kokoro TTS → Saves WAV file → Sends JSON back to User)
       │
       ▼
[User Hears Response 🔊]
```
