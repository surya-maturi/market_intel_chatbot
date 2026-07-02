from typing import Literal

from pydantic import BaseModel


class KeyStats(BaseModel):
    post_count: int
    avg_sentiment: float
    positive_pct: float
    negative_pct: float


class SourceCitation(BaseModel):
    title: str
    url: str
    sentiment: Literal["positive", "negative", "neutral"]


class SynthesisResult(BaseModel):
    headline: str
    summary: str
    sentiment_label: Literal["positive", "negative", "mixed", "neutral"]
    key_stats: KeyStats
    recommendations: list[str]
    sources: list[SourceCitation]
