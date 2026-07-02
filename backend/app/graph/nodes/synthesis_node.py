from app.core.constants import SYNTHESIS_SOURCE_COUNT, SYNTHESIS_TOP_POSTS
from app.graph.state import ChatState
from app.schemas.sentiment import SentimentResult
from app.schemas.synthesis import KeyStats, SourceCitation, SynthesisResult
from app.services import demo_data
from app.services.perplexity_client import PerplexityClient

_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "summary": {"type": "string"},
        "sentiment_label": {"type": "string", "enum": ["positive", "negative", "mixed", "neutral"]},
        "recommendations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["headline", "summary", "sentiment_label", "recommendations"],
}

_SYSTEM_PROMPT = """You are a market intelligence assistant for startup founders. You are given a set of \
recent Reddit posts about a topic, plus an aggregate sentiment reading computed from them. Write a concise, \
actionable synthesis for a founder deciding what to do next.

Respond with a single JSON object: headline (one sentence), summary (2-4 sentences grounded in the posts \
provided, do not invent facts not present in the posts), sentiment_label (positive|negative|mixed|neutral), \
recommendations (2-5 short actionable bullet points for a startup founder)."""


def make_synthesize(client: PerplexityClient):
    async def synthesize(state: ChatState) -> dict:
        sentiment: SentimentResult = state["sentiment"]
        posts = state.get("posts", [])
        top_posts = sorted(posts, key=lambda p: p.score + p.num_comments, reverse=True)[
            :SYNTHESIS_TOP_POSTS
        ]
        prompt = _build_prompt(state["user_query"], state.get("intent", ""), top_posts, sentiment)

        async def live_call() -> dict:
            return await client.chat_json(_SYSTEM_PROMPT, prompt, _SCHEMA, "synthesis_result")

        def demo_call() -> dict:
            return _templated_demo(state, sentiment)

        raw, used_demo = await client.call_with_fallback(
            "synthesis", client.is_configured(), live_call, demo_call
        )

        compound_by_title = {ps.title: ps.compound for ps in sentiment.top_posts}
        sources = [
            SourceCitation(
                title=p.title,
                url=f"https://reddit.com{p.permalink}" if p.permalink.startswith("/") else p.permalink,
                sentiment=_bucket(compound_by_title.get(p.title, 0.0)),
            )
            for p in top_posts[:SYNTHESIS_SOURCE_COUNT]
        ]

        result = SynthesisResult(
            headline=raw["headline"],
            summary=raw["summary"],
            sentiment_label=raw["sentiment_label"],
            key_stats=KeyStats(
                post_count=sentiment.post_count,
                avg_sentiment=sentiment.weighted_avg,
                positive_pct=sentiment.positive_pct,
                negative_pct=sentiment.negative_pct,
            ),
            recommendations=raw["recommendations"],
            sources=sources,
        )

        demo_flags = dict(state.get("demo_flags", {}))
        demo_flags["synthesis"] = used_demo

        return {"synthesis": result, "demo_flags": demo_flags}

    return synthesize


def _bucket(compound: float) -> str:
    if compound > 0.05:
        return "positive"
    if compound < -0.05:
        return "negative"
    return "neutral"


def _build_prompt(query: str, intent: str, top_posts: list, sentiment: SentimentResult) -> str:
    lines = [
        f"User query: {query}",
        f"Detected intent: {intent}",
        (
            f"Weighted sentiment: {sentiment.label} (avg={sentiment.weighted_avg:.2f}, "
            f"{sentiment.post_count} posts, {sentiment.positive_pct}% positive / "
            f"{sentiment.negative_pct}% negative)"
        ),
        "",
        "Top posts:",
    ]
    for p in top_posts:
        snippet = (p.selftext or "")[:200]
        lines.append(f'- "{p.title}" (score={p.score}, comments={p.num_comments}) {snippet}')
    return "\n".join(lines)


def _templated_demo(state: ChatState, sentiment: SentimentResult) -> dict:
    templates = demo_data.load_synthesis_demo()
    topic = ", ".join(state.get("topic_keywords") or [state["user_query"]])
    return {
        "headline": templates["headline_template"].format(topic=topic),
        "summary": templates["summary_template"].format(
            topic=topic,
            post_count=sentiment.post_count,
            sentiment_label=sentiment.label,
            avg_sentiment=f"{sentiment.weighted_avg:.2f}",
        ),
        "sentiment_label": sentiment.label,
        "recommendations": templates["recommendations"],
    }
