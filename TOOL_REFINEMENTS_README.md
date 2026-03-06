# Tool Refinements

This branch (`tool_refinement`) implements key improvements to the Voice Capstone's tool execution pipeline, based on the principle of increasing deterministic routing and reducing LLM hallucination.

## Implemented Upgrades

1. **Robust OpenFDA Fallback (Insight #10)**
   - Modified `medicine_classifier_tool.py`.
   - If the primary Gemini Vision classifier fails to identify a drug or returns "Unknown", it automatically falls back to the OpenFDA API (`medical_api_tool.py`).
   - Parses the government label data back into the strict JSON format required by the frontend UI, preventing silent failures.

2. **Standardized Tool Outputs & Error Handling (Insight #7 & #16)**
   - All tools now return a standardized Pydantic `ToolOutput` model consisting of `tool_name`, `result`, `success`, `confidence`, and `error`.
   - Fixed a core crashing bug in `medical_api_tool.py` when OpenFDA had zero results.
   - If a tool fails cleanly, the aggregator will cleanly say "I was not able to find info" instead of crashing the pipeline.

3. **Deterministic Haversine Distance Ranking (Insight #12)**
   - Upgraded `nearby_clinic_tool.py`.
   - Computes exact "as the crow flies" distance in kilometers from the user's GPS coordinates using the mathematical Haversine formula instead of blindly accepting the first 10 random API responses.
   - Filters, deduplicates, and sorts to guarantee only the 5 geographically closest clinics are returned, passing precise `distance_km` values to the LLM.

## Next Steps Planned
- Move health monitoring generic thresholds entirely out of the Prompt and into pure Python logic (Insight #11).
