import math

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.graph.state import ChatState
from app.schemas.sentiment import PostSentiment, SentimentResult

_analyzer = SentimentIntensityAnalyzer()


async def analyze_sentiment(state: ChatState) -> dict:
    posts = state.get("posts", [])
    demo_flags = dict(state.get("demo_flags", {}))
    demo_flags["sentiment"] = demo_flags.get("reddit", False)

    if not posts:
        empty = SentimentResult(
            raw_scores=[],
            weighted_avg=0.0,
            label="neutral",
            post_count=0,
            positive_pct=0.0,
            negative_pct=0.0,
            top_posts=[],
        )
        return {"sentiment": empty, "demo_flags": demo_flags}

    raw_scores: list[float] = []
    weighted_items: list[PostSentiment] = []
    total_weight = 0.0
    weighted_sum = 0.0
    positive = 0
    negative = 0

    for p in posts:
        text = f"{p.title} {p.selftext}".strip()
        compound = _analyzer.polarity_scores(text)["compound"]
        raw_scores.append(compound)

        weight = math.log(1 + p.score + p.num_comments)
        weighted_sum += compound * weight
        total_weight += weight

        if compound > 0.05:
            positive += 1
        elif compound < -0.05:
            negative += 1

        weighted_items.append(
            PostSentiment(
                title=p.title,
                compound=compound,
                score=p.score,
                num_comments=p.num_comments,
                weight=weight,
                url=p.permalink,
            )
        )

    weighted_avg = weighted_sum / total_weight if total_weight > 0 else 0.0
    label = "positive" if weighted_avg > 0.05 else "negative" if weighted_avg < -0.05 else "neutral"
    weighted_items.sort(key=lambda item: item.weight, reverse=True)

    result = SentimentResult(
        raw_scores=raw_scores,
        weighted_avg=weighted_avg,
        label=label,
        post_count=len(posts),
        positive_pct=round(100 * positive / len(posts), 1),
        negative_pct=round(100 * negative / len(posts), 1),
        top_posts=weighted_items[:10],
    )

    return {"sentiment": result, "demo_flags": demo_flags}
