from unittest.mock import AsyncMock

import pytest

from app.config import Settings
from app.graph.nodes.intent_node import make_classify_intent
from app.services.perplexity_client import PerplexityClient


def _client(raw: dict | None = None, raise_exc: Exception | None = None) -> PerplexityClient:
    client = PerplexityClient(Settings(_env_file=None, perplexity_api_key="test-key"))
    if raise_exc is not None:
        client.chat_json = AsyncMock(side_effect=raise_exc)
    else:
        client.chat_json = AsyncMock(return_value=raw)
    return client


@pytest.mark.parametrize(
    "query,raw_response,expected_intent",
    [
        (
            "Is remote work becoming more popular?",
            {
                "intent": "trend",
                "entity": None,
                "topic_keywords": ["remote work"],
                "confidence": 0.9,
                "reasoning": "",
            },
            "trend",
        ),
        (
            "What do people think about Notion's pricing?",
            {
                "intent": "sentiment",
                "entity": None,
                "topic_keywords": ["Notion pricing"],
                "confidence": 0.85,
                "reasoning": "",
            },
            "sentiment",
        ),
        (
            "Tell me about Figma as a company",
            {
                "intent": "competitor",
                "entity": "Figma",
                "topic_keywords": [],
                "confidence": 0.95,
                "reasoning": "",
            },
            "competitor",
        ),
    ],
)
async def test_classify_intent_clear_cases(query, raw_response, expected_intent):
    node = make_classify_intent(_client(raw=raw_response))
    result = await node({"user_query": query})
    assert result["intent"] == expected_intent
    assert result["demo_flags"]["intent"] is False


async def test_classify_intent_low_confidence_routes_to_unknown():
    raw = {"intent": "trend", "entity": None, "topic_keywords": [], "confidence": 0.2, "reasoning": "unsure"}
    node = make_classify_intent(_client(raw=raw))
    result = await node({"user_query": "asdkjaslkdj"})
    assert result["intent"] == "unknown"


async def test_classify_intent_competitor_without_entity_routes_to_unknown():
    raw = {"intent": "competitor", "entity": None, "topic_keywords": [], "confidence": 0.9, "reasoning": ""}
    node = make_classify_intent(_client(raw=raw))
    result = await node({"user_query": "tell me about this competitor"})
    assert result["intent"] == "unknown"


async def test_classify_intent_invalid_schema_falls_back_to_demo():
    node = make_classify_intent(_client(raw={"intent": "not-a-real-intent"}))
    result = await node({"user_query": "Is remote work trending?"})
    assert result["demo_flags"]["intent"] is True
    assert result["intent"] in {"trend", "sentiment", "competitor", "unknown"}


async def test_classify_intent_upstream_exception_falls_back_to_demo():
    node = make_classify_intent(_client(raise_exc=ValueError("could not parse JSON from LLM")))
    result = await node({"user_query": "Is remote work trending?"})
    assert result["demo_flags"]["intent"] is True
    assert result["intent"] in {"trend", "sentiment", "competitor", "unknown"}


async def test_classify_intent_not_configured_uses_demo_without_network_call():
    client = PerplexityClient(Settings(_env_file=None))  # no key
    client.chat_json = AsyncMock(side_effect=AssertionError("should never be called"))
    node = make_classify_intent(client)
    result = await node({"user_query": "Is remote work trending?"})
    assert result["demo_flags"]["intent"] is True
    client.chat_json.assert_not_called()
