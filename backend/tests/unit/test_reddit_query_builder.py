from types import SimpleNamespace

from app.config import Settings
from app.services.reddit_client import RedditClient, _filter_and_rank


def _submission(id_: str, title: str = "T", selftext: str = "", score: int = 10, comments: int = 5, removed=None):
    return SimpleNamespace(
        id=id_,
        title=title,
        selftext=selftext,
        score=score,
        num_comments=comments,
        permalink=f"/r/test/{id_}",
        subreddit="test",
        created_utc=0.0,
        removed_by_category=removed,
    )


def test_build_query_joins_keywords_as_quoted_or():
    client = RedditClient(Settings(_env_file=None))
    assert client.build_query(["remote work", "hybrid jobs"]) == '"remote work" OR "hybrid jobs"'


def test_build_query_empty_keywords_returns_empty_string():
    client = RedditClient(Settings(_env_file=None))
    assert client.build_query([]) == ""


def test_filter_drops_removed_empty_low_score_and_duplicate_ids():
    subs = [
        _submission("good1", title="Good post", score=50, comments=10),
        _submission("removed1", title="Removed post", score=100, comments=5, removed="moderator"),
        _submission("empty1", title="", selftext="", score=100, comments=5),
        _submission("lowscore1", title="Low score", score=0, comments=1),
        _submission("good1", title="Duplicate of good1", score=999, comments=1),
        _submission("good2", title="Another good post", score=20, comments=3),
    ]
    result = _filter_and_rank(subs)
    assert [p.id for p in result] == ["good1", "good2"]


def test_filter_ranks_by_score_descending():
    subs = [
        _submission("low", score=5),
        _submission("high", score=500),
        _submission("mid", score=50),
    ]
    result = _filter_and_rank(subs)
    assert [p.id for p in result] == ["high", "mid", "low"]
