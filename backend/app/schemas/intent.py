from typing import Literal

from pydantic import BaseModel, Field

IntentLabel = Literal["trend", "sentiment", "competitor", "unknown"]


class IntentClassification(BaseModel):
    intent: IntentLabel
    entity: str | None = Field(default=None, description="Company/brand name for competitor intent")
    topic_keywords: list[str] = Field(default_factory=list, description="2-6 short search phrases")
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""
