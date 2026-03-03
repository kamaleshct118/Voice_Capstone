"""
Tests for the MCP layer — intent classification and routing.
Uses unittest.mock to avoid real LLM/API calls.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.mcp.intent_classifier import classify_intent, IntentResult, VALID_INTENTS
from app.llm.client import LLMClient


def _make_llm(returns: str) -> LLMClient:
    """Create a mock LLM client that returns a given string."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.chat.return_value = returns
    return mock_llm


# ── Intent Classifier Tests ────────────────────────────────────────

def test_classify_medical_info():
    llm = _make_llm('{"intent": "medical_info", "entities": {"disease": "diabetes"}}')
    result = classify_intent("what is type 2 diabetes?", llm)
    assert result.intent == "medical_info"
    assert result.entities.get("disease") == "diabetes"


def test_classify_nearby_clinic():
    llm = _make_llm('{"intent": "nearby_clinic", "entities": {"location": "Chennai"}}')
    result = classify_intent("find clinics near Chennai", llm)
    assert result.intent == "nearby_clinic"


def test_classify_medicine_classifier():
    llm = _make_llm('{"intent": "medicine_classifier", "entities": {"drug": "paracetamol"}}')
    result = classify_intent("tell me about paracetamol", llm)
    assert result.intent == "medicine_classifier"
    assert result.entities.get("drug") == "paracetamol"


def test_classify_medical_news():
    llm = _make_llm('{"intent": "medical_news", "entities": {"disease": "cancer"}}')
    result = classify_intent("latest cancer research news", llm)
    assert result.intent == "medical_news"


def test_classify_consolidation():
    llm = _make_llm('{"intent": "consolidation_summary", "entities": {}}')
    result = classify_intent("summarize what we discussed", llm)
    assert result.intent == "consolidation_summary"


def test_fallback_on_invalid_intent():
    llm = _make_llm('{"intent": "unknown_gibberish", "entities": {}}')
    result = classify_intent("some query", llm)
    # Should fallback to medical_info
    assert result.intent == "medical_info"


def test_fallback_on_malformed_json():
    llm = _make_llm("sorry, I couldn't understand")
    result = classify_intent("some query", llm)
    assert result.intent in VALID_INTENTS  # Safe fallback


# ── Router Tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_router_routes_medical_info():
    from app.mcp.router import route_to_tools
    import fakeredis

    db1 = fakeredis.FakeRedis(decode_responses=True)
    db2 = fakeredis.FakeRedis(decode_responses=True)

    intent = IntentResult(
        intent="medical_info",
        entities={"disease": "diabetes"},
        raw_transcript="what is diabetes?",
    )

    with patch("app.tools.medical_api_tool.get_medical_info") as mock_tool:
        from app.mcp.router import ToolOutput
        mock_tool.return_value = ToolOutput(
            tool_name="medical_info",
            result={"description": "Diabetes is..."},
        )
        outputs = await route_to_tools(intent, db1, db2, "session-123")

    assert len(outputs) == 1
    assert outputs[0].tool_name == "medical_info"


@pytest.mark.asyncio
async def test_router_routes_nearby_clinic():
    from app.mcp.router import route_to_tools
    import fakeredis

    db1 = fakeredis.FakeRedis(decode_responses=True)
    db2 = fakeredis.FakeRedis(decode_responses=True)

    intent = IntentResult(
        intent="nearby_clinic",
        entities={"location": "Chennai"},
        raw_transcript="find clinics near Chennai",
    )

    with patch("app.tools.nearby_clinic_tool.find_nearby_clinics") as mock_tool:
        from app.mcp.router import ToolOutput
        mock_tool.return_value = ToolOutput(
            tool_name="nearby_clinic",
            result={"clinics": []},
            map_data={"type": "clinics", "locations": []},
        )
        outputs = await route_to_tools(intent, db1, db2, "session-456")

    assert outputs[0].tool_name == "nearby_clinic"
