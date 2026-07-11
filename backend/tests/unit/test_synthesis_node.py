from unittest.mock import AsyncMock

from app.config import Settings
from app.graph.nodes.synthesis_node import _build_prompt, make_synthesize
from app.schemas.reddit import RedditPost
from app.schemas.sentiment import SentimentResult
from app.services.perplexity_client import PerplexityClient


def _post(title: str, score: int = 10, comments: int = 1) -> RedditPost:
    return RedditPost(id=title[:8], title=title, selftext="", score=score, num_comments=comments)


def _sentiment(post_count: int = 3) -> SentimentResult:
    return SentimentResult(
        raw_scores=[0.0] * post_count,
        weighted_avg=0.0,
        label="neutral",
        post_count=post_count,
        positive_pct=0.0,
        negative_pct=0.0,
        top_posts=[],
    )


def _client(raw: dict) -> PerplexityClient:
    client = PerplexityClient(Settings(_env_file=None, perplexity_api_key="test-key"))
    client.chat_json = AsyncMock(return_value=raw)
    return client


def _state(posts):
    return {"user_query": "is X trending", "intent": "trend", "posts": posts, "sentiment": _sentiment(len(posts)), "demo_flags": {}}


async def test_synthesize_uses_model_cited_posts_as_sources():
    posts = [_post("First post", score=5), _post("Second post", score=100), _post("Third post", score=1)]
    # synthesize() sorts posts by engagement before numbering them for the prompt, so
    # [Second(100), First(5), Third(1)] -> [1]=Second, [2]=First, [3]=Third. Citing [2]
    # (not the top-ranked post) proves sources come from the model's citation, not just
    # the engagement heuristic reproducing itself.
    raw = {
        "headline": "h",
        "summary": "s",
        "sentiment_label": "neutral",
        "recommendations": ["r"],
        "cited_posts": [2],
    }
    node = make_synthesize(_client(raw))
    result = await node(_state(posts))

    titles = [s.title for s in result["synthesis"].sources]
    assert titles == ["First post"]


async def test_synthesize_falls_back_to_top_posts_when_model_cites_nothing():
    posts = [_post("Low engagement", score=1), _post("High engagement", score=500)]
    raw = {
        "headline": "h",
        "summary": "not enough discussion to draw a conclusion",
        "sentiment_label": "neutral",
        "recommendations": ["r"],
        "cited_posts": [],
    }
    node = make_synthesize(_client(raw))
    result = await node(_state(posts))

    titles = [s.title for s in result["synthesis"].sources]
    assert titles == ["High engagement", "Low engagement"]


async def test_synthesize_drops_out_of_range_and_malformed_citations():
    posts = [_post("Only post", score=5)]
    raw = {
        "headline": "h",
        "summary": "s",
        "sentiment_label": "neutral",
        "recommendations": ["r"],
        "cited_posts": [99, "not-an-int", 1, 1],  # out of range, wrong type, valid, duplicate
    }
    node = make_synthesize(_client(raw))
    result = await node(_state(posts))

    titles = [s.title for s in result["synthesis"].sources]
    assert titles == ["Only post"]


async def test_synthesize_demo_mode_ignores_any_cited_posts_field():
    # Demo mode's templated response never includes cited_posts, but even if it did,
    # there's no real model attribution behind it in demo mode - must use the heuristic.
    posts = [_post("Demo post A", score=1), _post("Demo post B", score=50)]
    client = PerplexityClient(Settings(_env_file=None))  # no key configured -> demo mode
    node = make_synthesize(client)
    result = await node(_state(posts))

    assert result["demo_flags"]["synthesis"] is True
    titles = [s.title for s in result["synthesis"].sources]
    assert titles == ["Demo post B", "Demo post A"]


def test_prompt_numbers_posts_so_the_model_can_cite_them():
    posts = [_post("Alpha"), _post("Beta")]
    prompt = _build_prompt("query", "trend", posts, _sentiment(2))
    assert '[1] "Alpha"' in prompt
    assert '[2] "Beta"' in prompt


def test_prompt_notes_when_no_posts_are_available():
    prompt = _build_prompt("query", "trend", [], _sentiment(0))
    assert "No posts were found for this topic." in prompt
