from app.graph.graph import build_graph


async def test_competitor_query_visits_expected_node_sequence(fake_settings):
    bundle = build_graph(fake_settings)
    visited = []
    async for chunk in bundle.compiled.astream(
        {"session_id": "s", "user_query": "Tell me about Figma as a company"}, stream_mode="updates"
    ):
        visited.append(next(iter(chunk)))
    await bundle.aclose()

    assert visited == ["classify_intent", "fetch_company"]


async def test_competitor_query_produces_company_profile(fake_settings):
    bundle = build_graph(fake_settings)
    final_state = await bundle.compiled.ainvoke(
        {"session_id": "s", "user_query": "Tell me about Figma as a company"}
    )
    await bundle.aclose()

    assert final_state["intent"] == "competitor"
    profile = final_state["company_profile"]
    assert profile is not None
    assert profile.name
    assert final_state["demo_flags"]["company"] is True
