# ──────────────────────────────────────────────────────────────────
# DEPRECATED: medicine_availability_tool.py
#
# This module has been REMOVED from the system as of v2.0.
# Medicine recommendation/availability has been replaced by:
#   → app/tools/medicine_classifier_tool.py
#
# The new tool classifies medicines by name, text, or image using
# Gemini Vision API and returns structured educational information.
# It does NOT suggest dosages, prescribe, or recommend medicines.
# ──────────────────────────────────────────────────────────────────

raise ImportError(
    "medicine_availability_tool is deprecated and removed. "
    "Use app.tools.medicine_classifier_tool instead."
)
