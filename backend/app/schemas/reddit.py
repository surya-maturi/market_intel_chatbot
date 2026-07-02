from pydantic import BaseModel


class RedditPost(BaseModel):
    id: str
    title: str
    selftext: str = ""
    score: int = 0
    num_comments: int = 0
    permalink: str = ""
    subreddit: str = ""
    created_utc: float = 0.0


class RedditFetchResult(BaseModel):
    posts: list[RedditPost]
    query: str
    used_demo: bool = False
