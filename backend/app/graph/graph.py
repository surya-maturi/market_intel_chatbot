from dataclasses import dataclass

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.config import Settings
from app.graph.nodes.company_node import make_fetch_company
from app.graph.nodes.fallback_node import clarify
from app.graph.nodes.intent_node import make_classify_intent
from app.graph.nodes.reddit_node import make_fetch_reddit
from app.graph.nodes.sentiment_node import analyze_sentiment
from app.graph.nodes.synthesis_node import make_synthesize
from app.graph.state import ChatState
from app.services.crunchbase_client import CrunchbaseClient
from app.services.pdl_client import PDLClient
from app.services.perplexity_client import PerplexityClient
from app.services.reddit_client import RedditClient

# Node names are deliberately distinct from ChatState field names (LangGraph
# forbids a node id that collides with a state key, e.g. "intent"/"sentiment").
# Deterministic routing table, also used by the API layer to synthesize
# "started" SSE events one step ahead of stream_mode="updates" chunks.
ROUTE_FROM_INTENT = {"trend": "fetch_reddit", "sentiment": "fetch_reddit", "competitor": "fetch_company"}
NEXT_NODE = {"fetch_reddit": "analyze_sentiment", "analyze_sentiment": "synthesize"}
TERMINAL_NODES = {"synthesize", "fetch_company", "clarify"}


def route_by_intent(state: ChatState) -> str:
    return ROUTE_FROM_INTENT.get(state.get("intent", "unknown"), "clarify")


@dataclass
class GraphBundle:
    compiled: CompiledStateGraph
    perplexity: PerplexityClient
    pdl: PDLClient
    reddit: RedditClient
    crunchbase: CrunchbaseClient

    async def aclose(self) -> None:
        await self.perplexity.aclose()
        await self.pdl.aclose()


def build_graph(settings: Settings) -> GraphBundle:
    perplexity = PerplexityClient(settings)
    reddit = RedditClient(settings)
    pdl = PDLClient(settings)
    crunchbase = CrunchbaseClient(settings)

    graph = StateGraph(ChatState)
    graph.add_node("classify_intent", make_classify_intent(perplexity))
    graph.add_node("fetch_reddit", make_fetch_reddit(reddit))
    graph.add_node("analyze_sentiment", analyze_sentiment)
    graph.add_node("synthesize", make_synthesize(perplexity))
    graph.add_node("fetch_company", make_fetch_company(pdl, crunchbase))
    graph.add_node("clarify", clarify)

    graph.set_entry_point("classify_intent")
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {"fetch_reddit": "fetch_reddit", "fetch_company": "fetch_company", "clarify": "clarify"},
    )
    graph.add_edge("fetch_reddit", "analyze_sentiment")
    graph.add_edge("analyze_sentiment", "synthesize")
    graph.add_edge("synthesize", END)
    graph.add_edge("fetch_company", END)
    graph.add_edge("clarify", END)

    compiled = graph.compile()
    return GraphBundle(compiled=compiled, perplexity=perplexity, pdl=pdl, reddit=reddit, crunchbase=crunchbase)
