from app.core.constants import INTENT_CONFIDENCE_THRESHOLD
from app.graph.state import ChatState
from app.schemas.intent import IntentClassification
from app.services import demo_data
from app.services.perplexity_client import PerplexityClient

_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": ["trend", "sentiment", "competitor", "unknown"]},
        "entity": {"type": ["string", "null"]},
        "topic_keywords": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
        "reasoning": {"type": "string"},
    },
    "required": ["intent", "topic_keywords", "confidence"],
}

_SYSTEM_PROMPT = """You classify a startup founder's question into one of four research intents.

- "trend": the user wants aggregate topic momentum/discussion volume (e.g. "is X becoming more popular", "what's the buzz around Y").
- "sentiment": the user wants opinion polarity about one specific thing (e.g. "how do people feel about X", "is the reaction to Y positive or negative").
- "competitor": the user wants information about a specific company (headcount, funding, revenue, description).
- "unknown": the request doesn't fit any of the above or is too vague to act on.

Examples:
Q: "Is remote work becoming more popular?" -> {"intent": "trend", "entity": null, "topic_keywords": ["remote work"], "confidence": 0.9, "reasoning": "asks about momentum over time"}
Q: "What do people think about Notion's pricing changes?" -> {"intent": "sentiment", "entity": null, "topic_keywords": ["Notion pricing"], "confidence": 0.88, "reasoning": "asks for opinion polarity"}
Q: "Tell me about Figma as a company" -> {"intent": "competitor", "entity": "Figma", "topic_keywords": [], "confidence": 0.95, "reasoning": "asks about a specific company"}
Q: "hello" -> {"intent": "unknown", "entity": null, "topic_keywords": [], "confidence": 0.1, "reasoning": "too vague to act on"}

Respond with a single JSON object matching the provided schema. topic_keywords should be 2-6 short search phrases (not a full sentence) when intent is "trend" or "sentiment"."""


def make_classify_intent(client: PerplexityClient):
    async def classify_intent(state: ChatState) -> dict:
        async def live_call() -> IntentClassification:
            raw = await client.chat_json(
                _SYSTEM_PROMPT, state["user_query"], _SCHEMA, "intent_classification"
            )
            return IntentClassification.model_validate(raw)

        def demo_call() -> IntentClassification:
            return _local_heuristic_classify(state["user_query"])

        result, used_demo = await client.call_with_fallback(
            "intent", client.is_configured(), live_call, demo_call
        )

        if result.confidence < INTENT_CONFIDENCE_THRESHOLD:
            result = result.model_copy(update={"intent": "unknown"})

        if result.intent == "competitor" and not (result.entity or "").strip():
            result = result.model_copy(update={"intent": "unknown"})

        demo_flags = dict(state.get("demo_flags", {}))
        demo_flags["intent"] = used_demo

        return {
            "intent": result.intent,
            "intent_confidence": result.confidence,
            "entity": result.entity,
            "topic_keywords": result.topic_keywords,
            "demo_flags": demo_flags,
        }

    return classify_intent


def _local_heuristic_classify(query: str) -> IntentClassification:
    demo = demo_data.load_intent_demo()
    lowered = query.lower()

    if any(w in lowered for w in demo["competitor_signal_words"]):
        words = query.split()
        # Skip index 0: sentence-initial capitalization isn't a signal of a proper noun.
        capitalized = [w.strip("?.,!\"'") for i, w in enumerate(words) if i > 0 and w[:1].isupper()]
        entity = " ".join(capitalized) if capitalized else query.strip()
        return IntentClassification(intent="competitor", entity=entity, topic_keywords=[], confidence=0.6)

    intent = "trend" if any(w in lowered for w in demo["trend_signal_words"]) else demo["default_intent"]
    stopwords = set(demo["stopwords"])
    words = [w.strip("?.,!\"'") for w in query.split() if w.lower() not in stopwords]
    words = [w for w in words if w]
    # A short 2-word phrase, not individual words and not the whole remaining
    # sentence: OR-ing single generic words (e.g. "work" OR "more") matches
    # almost anything, while an exact-phrase match on a long tail (5+ words)
    # matches almost nothing. Two words is the sweet spot for Reddit's
    # phrase search on a hand-rolled fallback like this one.
    topic_keywords = [" ".join(words[:2])] if words else [query.strip()]
    return IntentClassification(intent=intent, entity=None, topic_keywords=topic_keywords, confidence=0.55)
