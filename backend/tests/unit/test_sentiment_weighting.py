import math

import pytest
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.graph.nodes.sentiment_node import analyze_sentiment
from app.schemas.reddit import RedditPost


def _post(title: str, selftext: str, score: int, comments: int) -> RedditPost:
    return RedditPost(
        id=title[:8],
        title=title,
        selftext=selftext,
        score=score,
        num_comments=comments,
        permalink=f"/r/test/{title[:8]}",
        subreddit="test",
        created_utc=0.0,
    )


async def test_weighted_average_matches_hand_computed_value():
    posts = [
        _post("Great news everyone", "This is fantastic and amazing", 100, 20),
        _post("Terrible outcome", "This is awful and disappointing", 10, 2),
    ]
    result = await analyze_sentiment({"posts": posts, "demo_flags": {}})
    sentiment = result["sentiment"]

    analyzer = SentimentIntensityAnalyzer()
    c0 = analyzer.polarity_scores("Great news everyone This is fantastic and amazing")["compound"]
    c1 = analyzer.polarity_scores("Terrible outcome This is awful and disappointing")["compound"]
    w0 = math.log(1 + 100 + 20)
    w1 = math.log(1 + 10 + 2)
    expected = (c0 * w0 + c1 * w1) / (w0 + w1)

    assert sentiment.weighted_avg == pytest.approx(expected, abs=1e-6)
    assert sentiment.post_count == 2


async def test_empty_post_list_returns_zeroed_result_without_division_error():
    result = await analyze_sentiment({"posts": [], "demo_flags": {}})
    sentiment = result["sentiment"]
    assert sentiment.post_count == 0
    assert sentiment.weighted_avg == 0.0
    assert sentiment.label == "neutral"
    assert sentiment.top_posts == []


async def test_demo_flag_mirrors_reddit_flag():
    posts = [_post("Neutral title", "", 5, 1)]
    result = await analyze_sentiment({"posts": posts, "demo_flags": {"reddit": True}})
    assert result["demo_flags"]["sentiment"] is True

    result2 = await analyze_sentiment({"posts": posts, "demo_flags": {"reddit": False}})
    assert result2["demo_flags"]["sentiment"] is False
