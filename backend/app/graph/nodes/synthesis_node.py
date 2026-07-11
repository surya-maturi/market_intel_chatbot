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
        "cited_posts": {"type": "array", "items": {"type": "integer"}},
    },
    "required": ["headline", "summary", "sentiment_label", "recommendations", "cited_posts"],
}

_SYSTEM_PROMPT = """You are a market intelligence assistant for startup founders. You are given a numbered \
list of recent Reddit posts about a topic, plus an aggregate sentiment reading computed from them. Write a \
concise, actionable synthesis for a founder deciding what to do next.

Ground every claim in the summary in one or more of the numbered posts - do not invent facts, statistics, or \
events that are not present in the posts provided. If no posts are provided, or none of them say anything \
substantive about the topic, say plainly that there isn't enough Reddit discussion to draw a conclusion \
instead of inventing one.

Respond with a single JSON object: headline (one sentence), summary (2-4 sentences), sentiment_label \
(positive|negative|mixed|neutral), recommendations (2-5 short actionable bullet points for a startup founder), \
cited_posts (a list of the post numbers, e.g. [1, 3], that the summary actually draws on - empty if none)."""


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
        sources = _resolve_sources(raw, top_posts, compound_by_title, used_demo)

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


def _resolve_sources(
    raw: dict, top_posts: list, compound_by_title: dict, used_demo: bool
) -> list[SourceCitation]:
    """Prefer the posts the model says it actually grounded the summary in. Demo mode
    has no model attribution to draw on, and a model that cited nothing usable falls
    back to the highest-engagement posts rather than showing no sources at all."""
    cited = [] if used_demo else _valid_cited_posts(raw.get("cited_posts"), len(top_posts))
    chosen = [top_posts[i - 1] for i in cited] if cited else top_posts[:SYNTHESIS_SOURCE_COUNT]

    return [
        SourceCitation(
            title=p.title,
            url=f"https://reddit.com{p.permalink}" if p.permalink.startswith("/") else p.permalink,
            sentiment=_bucket(compound_by_title.get(p.title, 0.0)),
        )
        for p in chosen[:SYNTHESIS_SOURCE_COUNT]
    ]


def _valid_cited_posts(raw_cited, post_count: int) -> list[int]:
    if not isinstance(raw_cited, list):
        return []
    seen: set[int] = set()
    ordered: list[int] = []
    for value in raw_cited:
        if isinstance(value, int) and 1 <= value <= post_count and value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


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
        "Numbered posts (cite these by number in cited_posts):" if top_posts else "No posts were found for this topic.",
    ]
    for i, p in enumerate(top_posts, start=1):
        snippet = (p.selftext or "")[:200]
        lines.append(f'[{i}] "{p.title}" (score={p.score}, comments={p.num_comments}) {snippet}')
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
