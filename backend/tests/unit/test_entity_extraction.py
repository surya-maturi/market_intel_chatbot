from unittest.mock import AsyncMock

from app.config import Settings
from app.graph.nodes.intent_node import make_classify_intent
from app.services.perplexity_client import PerplexityClient


def _client(raw: dict) -> PerplexityClient:
    client = PerplexityClient(Settings(_env_file=None, perplexity_api_key="test-key"))
    client.chat_json = AsyncMock(return_value=raw)
    return client


async def test_competitor_entity_extracted_from_llm_response():
    raw = {"intent": "competitor", "entity": "Figma", "topic_keywords": [], "confidence": 0.9, "reasoning": ""}
    node = make_classify_intent(_client(raw))
    result = await node({"user_query": "Tell me about Figma"})
    assert result["entity"] == "Figma"
    assert result["intent"] == "competitor"


async def test_trend_topic_keywords_extracted_not_raw_sentence():
    query = "Are electric vehicles seeing wider adoption this year?"
    raw = {
        "intent": "trend",
        "entity": None,
        "topic_keywords": ["electric vehicles", "adoption"],
        "confidence": 0.9,
        "reasoning": "",
    }
    node = make_classify_intent(_client(raw))
    result = await node({"user_query": query})
    assert result["topic_keywords"] == ["electric vehicles", "adoption"]
    assert result["topic_keywords"] != [query]


async def test_competitor_empty_entity_routes_to_unknown():
    raw = {"intent": "competitor", "entity": "", "topic_keywords": [], "confidence": 0.9, "reasoning": ""}
    node = make_classify_intent(_client(raw))
    result = await node({"user_query": "tell me about a competitor"})
    assert result["intent"] == "unknown"
