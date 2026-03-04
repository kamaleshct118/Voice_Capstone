"""
Tests for the tool layer — medicine classifier and health monitor.
Uses unittest.mock to avoid real Gemini/API calls.
Uses fakeredis for Redis.
"""
import pytest
import fakeredis
from unittest.mock import MagicMock, patch

from app.tools.medicine_classifier_tool import classify_medicine
from app.tools.health_monitor_tool import threshold_check, log_health_entry, HealthLogEntry
from app.cache.db1_cag import build_cache_key, store_chunk
from app.cache.db0_context import get_health_logs


@pytest.fixture
def db1():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def db0():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def mock_gemini():
    mock = MagicMock()
    mock.classify_medicine_text.return_value = '''{
        "medicine_name": "Paracetamol",
        "chemical_composition": "Acetaminophen 500mg",
        "drug_category": "Analgesic / Antipyretic",
        "purpose": "Relief of mild to moderate pain and fever",
        "basic_safety_notes": "Avoid alcohol. Do not exceed recommended dose."
    }'''
    mock.analyze_medicine_image.return_value = '''{
        "medicine_name": "Amoxicillin",
        "chemical_composition": "Amoxicillin trihydrate 250mg",
        "drug_category": "Antibiotic",
        "purpose": "Treatment of bacterial infections",
        "basic_safety_notes": "Complete the full course. Avoid if penicillin allergic."
    }'''
    return mock


# ── Medicine Classifier Tests ──────────────────────────────────────

def test_text_mode_cache_miss_calls_gemini(db1, mock_gemini):
    """On cache miss, Gemini is called and result cached."""
    output = classify_medicine("text", "paracetamol", None, db1, mock_gemini)
    mock_gemini.classify_medicine_text.assert_called_once()
    assert output.tool_name == "medicine_classifier"
    assert output.medicine_data is not None
    assert output.medicine_data["medicine_name"] == "Paracetamol"


def test_text_mode_cache_hit_skips_gemini(db1, mock_gemini):
    """On cache hit, Gemini is NOT called."""
    # Pre-populate cache
    key = build_cache_key("medicine_classifier", "paracetamol")
    cached_data = {
        "medicine_name": "Paracetamol",
        "chemical_composition": "Acetaminophen 500mg",
        "drug_category": "Analgesic",
        "purpose": "Pain relief",
        "basic_safety_notes": "Avoid alcohol.",
    }
    store_chunk(db1, key, cached_data, ttl=3600)

    output = classify_medicine("text", "paracetamol", None, db1, mock_gemini)
    mock_gemini.classify_medicine_text.assert_not_called()
    assert output.medicine_data["medicine_name"] == "Paracetamol"


def test_image_mode_calls_vision(db1, mock_gemini):
    """Image mode calls analyze_medicine_image, not text classifier."""
    fake_image = b"\x89PNG\r\n\x1a\n"  # PNG magic bytes
    output = classify_medicine("image", None, fake_image, db1, mock_gemini)
    mock_gemini.analyze_medicine_image.assert_called_once()
    assert output.medicine_data["medicine_name"] == "Amoxicillin"


def test_image_mode_not_cached(db1, mock_gemini):
    """Image results are NOT cached in DB1 (not reproducible by key)."""
    fake_image = b"\xff\xd8\xff"  # JPEG magic bytes
    classify_medicine("image", None, fake_image, db1, mock_gemini)
    # Image mode uses no key — DB1 should have no medicine_classifier keys
    assert db1.dbsize() == 0


def test_disclaimer_always_present(db1, mock_gemini):
    """Disclaimer must be present in every medicine classifier response."""
    for mode in ("text", "voice"):
        output = classify_medicine(mode, "ibuprofen", None, db1, mock_gemini)
        assert "disclaimer" in output.medicine_data
        assert len(output.medicine_data["disclaimer"]) > 10


def test_no_dosage_in_output(db1, mock_gemini):
    """Output must contain a disclaimer and must not include prescriptive dosage instructions."""
    output = classify_medicine("text", "paracetamol", None, db1, mock_gemini)
    medicine_str = str(output.medicine_data).lower()
    # Disclaimer must always be present
    assert "disclaimer" in output.medicine_data
    # No prescriptive dosage instructions (mg amounts, "twice daily", "tablets" etc.)
    assert "twice daily" not in medicine_str
    assert "mg per day" not in medicine_str
    assert "tablets per" not in medicine_str


# ── Health Monitor Tests ───────────────────────────────────────────

def test_threshold_check_normal_bp():
    logs = [{"systolic_bp": 115, "diastolic_bp": 75, "timestamp": "2026-01-01"}]
    flags = threshold_check(logs)
    assert len(flags) == 0


def test_threshold_check_warning_bp():
    logs = [{"systolic_bp": 125, "diastolic_bp": 75, "timestamp": "2026-01-01"}]
    flags = threshold_check(logs)
    assert any(f["field"] == "systolic_bp" and f["level"] == "warning" for f in flags)


def test_threshold_check_danger_bp():
    logs = [{"systolic_bp": 155, "diastolic_bp": 95, "timestamp": "2026-01-01"}]
    flags = threshold_check(logs)
    assert any(f["field"] == "systolic_bp" and f["level"] == "danger" for f in flags)
    assert any(f["field"] == "diastolic_bp" and f["level"] == "danger" for f in flags)


def test_threshold_check_diabetes_sugar():
    logs = [{"sugar_fasting": 130, "timestamp": "2026-01-01"}]
    flags = threshold_check(logs)
    assert any(f["field"] == "sugar_fasting" and f["level"] == "danger" for f in flags)


def test_log_health_entry_persists(db0):
    entry = HealthLogEntry(
        session_id="health-persist-test",
        condition="hypertension",
        systolic_bp=138,
        diastolic_bp=88,
    )
    log_health_entry(entry, db0)
    logs = get_health_logs(db0, "health-persist-test")
    assert len(logs) == 1
    assert logs[0]["systolic_bp"] == 138
