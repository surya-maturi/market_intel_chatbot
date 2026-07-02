from app.config import get_settings
from app.graph.graph import GraphBundle, build_graph

_bundle: GraphBundle | None = None


def get_graph_bundle() -> GraphBundle:
    global _bundle
    if _bundle is None:
        _bundle = build_graph(get_settings())
    return _bundle
