from pydantic import BaseModel


class PostSentiment(BaseModel):
    title: str
    compound: float
    score: int
    num_comments: int
    weight: float
    url: str = ""


class SentimentResult(BaseModel):
    raw_scores: list[float]
    weighted_avg: float
    label: str
    post_count: int
    positive_pct: float
    negative_pct: float
    top_posts: list[PostSentiment]
