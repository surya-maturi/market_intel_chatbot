from app.graph.graph import build_graph


async def test_trend_query_visits_expected_node_sequence(fake_settings):
    bundle = build_graph(fake_settings)
    visited = []
    async for chunk in bundle.compiled.astream(
        {"session_id": "s", "user_query": "Is remote work becoming more popular?"}, stream_mode="updates"
    ):
        visited.append(next(iter(chunk)))
    await bundle.aclose()

    assert visited == ["classify_intent", "fetch_reddit", "analyze_sentiment", "synthesize"]


async def test_trend_query_produces_well_formed_synthesis(fake_settings):
    bundle = build_graph(fake_settings)
    final_state = await bundle.compiled.ainvoke(
        {"session_id": "s", "user_query": "Is remote work becoming more popular?"}
    )
    await bundle.aclose()

    assert final_state["intent"] in {"trend", "sentiment"}
    synthesis = final_state["synthesis"]
    assert synthesis is not None
    assert synthesis.headline
    assert synthesis.recommendations
    assert len(synthesis.sources) > 0
    assert final_state["demo_flags"]["reddit"] is True
