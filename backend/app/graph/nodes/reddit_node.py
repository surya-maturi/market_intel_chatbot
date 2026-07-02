from app.graph.state import ChatState
from app.schemas.reddit import RedditPost
from app.services import demo_data
from app.services.fallback import call_with_fallback
from app.services.reddit_client import RedditClient


def make_fetch_reddit(client: RedditClient):
    async def fetch_reddit(state: ChatState) -> dict:
        topic_keywords = state.get("topic_keywords") or [state["user_query"]]
        query = client.build_query(topic_keywords)

        async def live_call() -> list[RedditPost]:
            return await client.search(topic_keywords)

        def demo_call() -> list[RedditPost]:
            return [RedditPost(**p) for p in demo_data.load_reddit_demo(topic_keywords)]

        posts, used_demo = await call_with_fallback(
            "reddit", client.is_configured(), live_call, demo_call
        )

        demo_flags = dict(state.get("demo_flags", {}))
        demo_flags["reddit"] = used_demo

        return {
            "posts": posts,
            "reddit_query": query,
            "demo_flags": demo_flags,
        }

    return fetch_reddit
