import praw
from utils.config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT

def fetch_reddit_posts(query: str, limit: int = 20):
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )
    posts = []
    for submission in reddit.subreddit("all").search(query, limit=limit, sort='new'):
        posts.append({"title": submission.title, "selftext": submission.selftext})
    return posts
