"""
Tests for the MCP layer — intent classification and routing.
Updated to match the refactored 5-intent architecture.
Uses unittest.mock to avoid real LLM/API calls.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.mcp.intent_classifier import classify_intent, IntentResult, VALID_INTENTS
from app.llm.client import LLMClient


def _make_llm(returns: str) -> LLMClient:
    """Create a mock LLM client that returns a given string."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.chat.return_value = returns
    return mock_llm


# ── Intent Classifier Tests ────────────────────────────────────────

def test_classify_medicine_info():
    llm = _make_llm('{"intent": "medicine_info", "entities": {"drug": "paracetamol"}}')
    result = classify_intent("tell me about paracetamol", llm)
    assert result.intent == "medicine_info"
    assert result.entities.get("drug") == "paracetamol"


def test_classify_medical_news():
    llm = _make_llm('{"intent": "medical_news", "entities": {"topic": "cancer"}}')
    result = classify_intent("latest cancer research news", llm)
    assert result.intent == "medical_news"


def test_classify_medical_report():
    llm = _make_llm('{"intent": "medical_report", "entities": {}}')
    result = classify_intent("generate my health report", llm)
    assert result.intent == "medical_report"


def test_classify_health_monitoring():
    llm = _make_llm('{"intent": "health_monitoring", "entities": {"topic": "blood pressure"}}')
    result = classify_intent("what was my blood pressure yesterday?", llm)
    assert result.intent == "health_monitoring"


def test_classify_general_conversation():
    llm = _make_llm('{"intent": "general_conversation", "entities": {}}')
    result = classify_intent("hello, how are you?", llm)
    assert result.intent == "general_conversation"


def test_fallback_on_invalid_intent():
    """Unknown intents from LLM should fall back to general_conversation."""
    llm = _make_llm('{"intent": "unknown_gibberish", "entities": {}}')
    result = classify_intent("some query", llm)
    assert result.intent == "general_conversation"


def test_fallback_on_malformed_json():
    """Malformed LLM response should fall back to a valid intent."""
    llm = _make_llm("sorry, I couldn't understand")
    result = classify_intent("some query", llm)
    assert result.intent in VALID_INTENTS


def test_all_valid_intents_defined():
    """Confirm the 5 required intents are registered."""
    expected = {
        "medicine_info", "medical_news", "medical_report",
        "health_monitoring", "general_conversation",
    }
    assert expected == set(VALID_INTENTS)


# ── Router Tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_router_routes_medicine_info():
    from app.mcp.router import route_to_tools, ToolOutput
    import fakeredis

    db1 = fakeredis.FakeRedis(decode_responses=True)
    db2 = fakeredis.FakeRedis(decode_responses=True)

    intent = IntentResult(
        intent="medicine_info",
        entities={"drug": "paracetamol"},
        raw_transcript="tell me about paracetamol",
    )

    with patch("app.tools.medicine_classifier_tool.classify_medicine") as mock_tool:
        mock_tool.return_value = ToolOutput(
            tool_name="medicine_info",
            result={"medicine_name": "Paracetamol"},
        )
        outputs = await route_to_tools(intent, db1, db2, "session-001")

    assert len(outputs) == 1
    assert outputs[0].tool_name == "medicine_info"


@pytest.mark.asyncio
async def test_router_routes_medical_news():
    from app.mcp.router import route_to_tools, ToolOutput
    import fakeredis

    db1 = fakeredis.FakeRedis(decode_responses=True)
    db2 = fakeredis.FakeRedis(decode_responses=True)

    intent = IntentResult(
        intent="medical_news",
        entities={"topic": "diabetes"},
        raw_transcript="latest diabetes news",
    )

    with patch("app.tools.news_tool.get_medical_news") as mock_tool:
        mock_tool.return_value = ToolOutput(
            tool_name="medical_news",
            result={"articles": []},
        )
        outputs = await route_to_tools(intent, db1, db2, "session-002")

    assert outputs[0].tool_name == "medical_news"


@pytest.mark.asyncio
async def test_router_routes_medical_report():
    from app.mcp.router import route_to_tools, ToolOutput
    import fakeredis

    db1 = fakeredis.FakeRedis(decode_responses=True)
    db2 = fakeredis.FakeRedis(decode_responses=True)

    intent = IntentResult(
        intent="medical_report",
        entities={},
        raw_transcript="generate my health report",
    )

    with patch("app.tools.report_tool.generate_medical_report") as mock_tool:
        mock_tool.return_value = ToolOutput(
            tool_name="medical_report",
            result={"total_interactions": 5},
        )
        outputs = await route_to_tools(intent, db1, db2, "session-003")

    assert outputs[0].tool_name == "medical_report"


@pytest.mark.asyncio
async def test_router_general_conversation_returns_empty():
    """general_conversation uses no tools — route_to_tools returns empty list."""
    from app.mcp.router import route_to_tools
    import fakeredis

    db1 = fakeredis.FakeRedis(decode_responses=True)
    db2 = fakeredis.FakeRedis(decode_responses=True)

    intent = IntentResult(
        intent="general_conversation",
        entities={},
        raw_transcript="hello",
    )

    outputs = await route_to_tools(intent, db1, db2, "session-004")
    assert outputs == []
