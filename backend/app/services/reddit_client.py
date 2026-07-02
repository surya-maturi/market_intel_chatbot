import asyncpraw

from app.config import Settings
from app.core.constants import REDDIT_FETCH_LIMIT, REDDIT_MIN_SCORE, REDDIT_TIME_FILTER, REDDIT_TOP_N
from app.schemas.reddit import RedditPost


class RedditClient:
    def __init__(self, settings: Settings):
        self._settings = settings

    def is_configured(self) -> bool:
        return bool(self._settings.reddit_client_id and self._settings.reddit_client_secret)

    def build_query(self, topic_keywords: list[str]) -> str:
        if not topic_keywords:
            return ""
        return " OR ".join(f'"{kw}"' for kw in topic_keywords)

    async def search(self, topic_keywords: list[str]) -> list[RedditPost]:
        query = self.build_query(topic_keywords)
        reddit = asyncpraw.Reddit(
            client_id=self._settings.reddit_client_id,
            client_secret=self._settings.reddit_client_secret,
            user_agent=self._settings.reddit_user_agent,
        )
        try:
            subreddit = await reddit.subreddit("all")
            raw_posts = [
                submission
                async for submission in subreddit.search(
                    query,
                    limit=REDDIT_FETCH_LIMIT,
                    sort="relevance",
                    time_filter=REDDIT_TIME_FILTER,
                )
            ]
            return _filter_and_rank(raw_posts)
        finally:
            await reddit.close()


def _filter_and_rank(submissions) -> list[RedditPost]:
    seen_ids: set[str] = set()
    filtered = []
    for s in submissions:
        if s.id in seen_ids:
            continue
        if getattr(s, "removed_by_category", None) is not None:
            continue
        if not (s.title or s.selftext):
            continue
        if (s.score or 0) < REDDIT_MIN_SCORE:
            continue
        seen_ids.add(s.id)
        filtered.append(s)

    filtered.sort(key=lambda s: s.score or 0, reverse=True)
    top = filtered[:REDDIT_TOP_N]

    return [
        RedditPost(
            id=s.id,
            title=s.title or "",
            selftext=(s.selftext or "")[:1000],
            score=s.score or 0,
            num_comments=s.num_comments or 0,
            permalink=s.permalink or "",
            subreddit=str(s.subreddit),
            created_utc=s.created_utc or 0.0,
        )
        for s in top
    ]
