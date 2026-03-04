"""
Tests for Redis cache layer (DB1 CAG tool cache + DB0 context/health logs).
Uses fakeredis for in-memory simulation — no real Redis needed.
"""
import time
import pytest
import fakeredis

from app.cache.db1_cag import build_cache_key, get_cached_chunk, store_chunk
from app.cache.db0_context import (
    get_context, append_context, clear_context,
    append_health_log, get_health_logs, clear_health_logs,
)


@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis(decode_responses=True)


# ── DB1 CAG Tests ─────────────────────────────────────────────────

def test_build_cache_key_deterministic():
    k1 = build_cache_key("medical_info", "diabetes ")
    k2 = build_cache_key("medical_info", " Diabetes")
    assert k1 == k2


def test_store_and_get_chunk(redis_client):
    key = build_cache_key("medical_info", "hypertension")
    data = {"description": "High blood pressure condition", "source": "OpenFDA"}
    store_chunk(redis_client, key, data, ttl=60)
    result = get_cached_chunk(redis_client, key)
    assert result is not None
    assert result["description"] == data["description"]


def test_cache_miss_returns_none(redis_client):
    key = build_cache_key("medical_info", "nonexistent_disease_xyz")
    result = get_cached_chunk(redis_client, key)
    assert result is None


def test_ttl_expires(redis_client):
    key = build_cache_key("medical_info", "short_lived")
    store_chunk(redis_client, key, {"data": "temporary"}, ttl=1)
    assert get_cached_chunk(redis_client, key) is not None
    time.sleep(1.1)
    assert get_cached_chunk(redis_client, key) is None


# ── DB0 Context Tests ───────────────────────────────────────────────────

def test_append_and_get_context(redis_client):
    session_id = "test-session-001"
    append_context(redis_client, session_id, "user", "What is diabetes?")
    append_context(redis_client, session_id, "assistant", "Diabetes is a chronic condition.")
    history = get_context(redis_client, session_id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"


def test_context_trim_to_max_turns(redis_client):
    session_id = "test-trim-001"
    for i in range(15):
        append_context(redis_client, session_id, "user", f"Message {i}", max_turns=10)
    history = get_context(redis_client, session_id)
    assert len(history) <= 10


def test_clear_context(redis_client):
    session_id = "test-clear-001"
    append_context(redis_client, session_id, "user", "hello")
    clear_context(redis_client, session_id)
    assert get_context(redis_client, session_id) == []


# ── DB0 Health Log Tests ─────────────────────────────────────────────────

def test_append_health_log(redis_client):
    session_id = "health-test-001"
    append_health_log(redis_client, session_id, {"systolic_bp": 120, "diastolic_bp": 80})
    logs = get_health_logs(redis_client, session_id)
    assert len(logs) == 1
    assert logs[0]["systolic_bp"] == 120
    assert "timestamp" in logs[0]


def test_get_health_logs_limit(redis_client):
    session_id = "health-test-002"
    for i in range(40):
        append_health_log(redis_client, session_id, {"weight_kg": 70 + i})
    logs = get_health_logs(redis_client, session_id, limit=30)
    assert len(logs) == 30


def test_clear_health_logs(redis_client):
    session_id = "health-clear-001"
    append_health_log(redis_client, session_id, {"systolic_bp": 130})
    clear_health_logs(redis_client, session_id)
    assert get_health_logs(redis_client, session_id) == []
