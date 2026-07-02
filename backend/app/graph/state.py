import operator
from typing import Annotated, TypedDict

from app.schemas.company import CompanyProfile
from app.schemas.reddit import RedditPost
from app.schemas.sentiment import SentimentResult
from app.schemas.synthesis import SynthesisResult


class ChatState(TypedDict, total=False):
    session_id: str
    user_query: str

    intent: str
    intent_confidence: float
    entity: str | None
    topic_keywords: list[str]

    reddit_query: str
    posts: list[RedditPost]

    sentiment: SentimentResult | None
    company_profile: CompanyProfile | None
    synthesis: SynthesisResult | None

    final_response_markdown: str
    demo_flags: dict[str, bool]
    errors: Annotated[list[str], operator.add]
