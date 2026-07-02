import json

import httpx

from app.db.session import init_db
from app.main import app


async def test_chat_stream_sse_sequence_and_persistence():
    init_db()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream(
            "POST", "/api/chat/stream", json={"message": "Is remote work trending?"}
        ) as response:
            assert response.status_code == 200
            buffer = ""
            async for chunk in response.aiter_text():
                buffer += chunk

    events = [
        json.loads(block[len("data: ") :])
        for block in buffer.strip().split("\n\n")
        if block.startswith("data: ")
    ]
    types = [e["type"] for e in events]

    assert types[0] == "session"
    assert types[-1] == "done"
    assert "result" in types
    assert types.count("step") >= 2

    session_id = events[0]["session_id"]

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        history_resp = await client.get(f"/api/chat/sessions/{session_id}/history")

    assert history_resp.status_code == 200
    messages = history_resp.json()["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[1]["used_demo_data"] is True


async def test_health_reports_demo_status_when_unconfigured():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["services"]["perplexity"] == "demo"
    assert body["services"]["reddit"] == "demo"
    assert body["services"]["pdl"] == "demo"
