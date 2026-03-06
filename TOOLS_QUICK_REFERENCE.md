# Tools Quick Reference Guide

## Tool Summary Table

| Tool # | Name | Intent | Cache | TTL | API Used |
|--------|------|--------|-------|-----|----------|
| 1 | Medicine Classifier | `medicine_info` | DB1 | 36h | Gemini Vision |
| 2 | Medical News | `medical_news` | DB1 | 36h | NewsAPI |
| 3 | Medical Report | `medical_report` | No | - | None (DB0 data) |
| 4 | Health Monitor | `health_monitoring` | No | - | None (DB0 data) |
| 5 | Nearby Clinic | `nearby_clinic` | No | - | Nominatim OSM |
| 6 | Consolidation | (implicit) | No | - | None (DB0 data) |

---

## Tool 1: Medicine Classifier

**File:** `backend/app/tools/medicine_classifier_tool.py`

**Trigger:** User asks about a medicine by name or uploads medicine photo

**Test Questions:**
- "What is paracetamol?"
- "Tell me about ibuprofen"
- "What is aspirin used for?"
- "Explain metformin"

**Input:** Medicine name (text) or image bytes

**Output:**
```json
{
  "medicine_name": "Paracetamol",
  "chemical_composition": "N-(4-hydroxyphenyl)acetamide",
  "drug_category": "Analgesic, Antipyretic",
  "purpose": "Pain relief and fever reduction",
  "basic_safety_notes": "Do not exceed 4g per day",
  "disclaimer": "Educational purposes only"
}
```

**Cache:** Redis DB1, key: `medicine_info:<hash>`, TTL: 36 hours

---

## Tool 2: Medical News

**File:** `backend/app/tools/news_tool.py`

**Trigger:** User asks for latest medical/pharmaceutical news

**Test Questions:**
- "Latest news on cancer treatment"
- "Recent medical news about diabetes"
- "What's new in cardiology?"

**Input:** Topic (disease/drug name)

**Output:**
```json
{
  "topic": "cancer treatment",
  "articles": [
    {
      "title": "New Breakthrough...",
      "description": "Researchers discover...",
      "url": "https://...",
      "published_at": "2026-03-04T10:30:00Z"
    }
  ],
  "source": "NewsAPI"
}
```

**Cache:** Redis DB1, key: `medical_news:<hash>`, TTL: 36 hours

---

## Tool 3: Medical Report Generator

**File:** `backend/app/tools/report_tool.py`

**Trigger:** User requests health summary/report

**Test Questions:**
- "Generate my medical report"
- "Show me my health summary"
- "What have we discussed?"

**Input:** Session ID

**Output:**
```json
{
  "session_id": "abc123",
  "generated_at": "2026-03-05T14:30:00Z",
  "total_interactions": 25,
  "topics_discussed": ["aspirin", "diabetes"],
  "health_metrics": {
    "latest_systolic_bp": 125,
    "latest_diastolic_bp": 82,
    "latest_fasting_sugar": 110
  }
}
```

**Cache:** No (always fresh data from DB0)

---

## Tool 4: Health Monitor

**File:** `backend/app/tools/health_monitor_tool.py`

**Trigger:** User asks about health metrics/trends

**Test Questions:**
- "How is my blood pressure?"
- "Show my health trends"
- "Am I improving?"

**Input:** Session ID

**Output:**
```json
{
  "summary": "Your BP has been stable...",
  "flagged_readings": [...],
  "diet_suggestions": [...],
  "lifestyle_recommendations": [...],
  "daily_checklist": [...]
}
```

**Cache:** No (real-time analysis)

**Features:**
- Threshold checking (BP, sugar)
- LLM-based trend analysis
- Daily checklist generation
- Excel export

---

## Tool 5: Nearby Clinic Search

**File:** `backend/app/tools/nearby_clinic_tool.py`

**Trigger:** User needs medical facility locations

**Test Questions:**
- "Find nearby clinics"
- "Where is the nearest hospital?"
- "I need immediate medical help"

**Input:** Location name or GPS coordinates

**Output:**
```json
{
  "location": "Coimbatore",
  "clinics": [
    {
      "name": "City General Hospital",
      "address": "123 Main St",
      "lat": 11.0168,
      "lng": 76.9558
    }
  ],
  "count": 10
}
```

**Cache:** No (real-time search)

---

## System Prompts Summary

### 1. Intent Classification
- **Model:** Llama 3.1 8B Instant
- **Purpose:** Classify user intent
- **Output:** `{intent, entities}`

### 2. Medicine Classifier
- **Model:** Gemini 2.0 Flash
- **Purpose:** Identify medicine from text/image
- **Output:** Structured medicine data

### 3. Response Aggregation
- **Model:** Llama 3.3 70B Versatile
- **Purpose:** Combine tool outputs
- **Output:** Voice-ready text

### 4. General Conversation
- **Model:** Llama 3.3 70B Versatile
- **Purpose:** Handle chitchat/Q&A
- **Output:** Conversational response

### 5. Health Analysis
- **Model:** Llama 3.3 70B Versatile
- **Purpose:** Analyze health trends
- **Output:** Structured health report

---

## Redis Database Keys

### DB0 (Conversation Cache - 30h TTL)
- `ctx:<session_id>` → Conversation history
- `health:<session_id>` → Health log entries
- `healthchat:<session_id>` → Health chat history

### DB1 (Tool Cache - 36h TTL)
- `medicine_info:<hash>` → Medicine classifications
- `medical_news:<hash>` → News articles
- `medical_info:<hash>` → OpenFDA drug data

---

## Testing Checklist

### Populate DB1 Cache

**Medicine Info:**
```
✓ "What is paracetamol?"
✓ "Tell me about ibuprofen"
✓ "What is aspirin used for?"
✓ "Explain metformin"
✓ "What is amoxicillin?"
```

**Medical News:**
```
✓ "Latest news on cancer treatment"
✓ "Recent medical news about diabetes"
✓ "What's new in cardiology?"
```

**Medical API:**
```
✓ "Side effects of metformin"
✓ "What are the warnings for aspirin?"
```

### Test All Tools

```
✓ Tool 1: Medicine classifier
✓ Tool 2: Medical news
✓ Tool 3: Medical report
✓ Tool 4: Health monitoring
✓ Tool 5: Nearby clinic search
✓ Tool 6: Consolidation summary
```

---

## Performance Benchmarks

| Operation | Cache HIT | Cache MISS |
|-----------|-----------|------------|
| Medicine Info | 1-2s | 3-5s |
| Medical News | 1-2s | 4-6s |
| Health Analysis | 3-4s | N/A |
| Medical Report | 2-3s | N/A |
| Clinic Search | 3-5s | N/A |

---

**Last Updated:** March 5, 2026
