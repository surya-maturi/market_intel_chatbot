import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, sessionmaker
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_graph_bundle
from app.db import crud
from app.db.session import get_session, get_session_factory
from app.graph.graph import NEXT_NODE, ROUTE_FROM_INTENT, GraphBundle
from app.schemas.chat import ChatHistoryResponse, ChatMessageOut, ChatRequest

router = APIRouter()
logger = logging.getLogger(__name__)

# graph node name -> key used in ChatState["demo_flags"]
NODE_TO_FLAG_KEY = {
    "classify_intent": "intent",
    "fetch_reddit": "reddit",
    "analyze_sentiment": "sentiment",
    "synthesize": "synthesis",
    "fetch_company": "company",
}


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, default=str)}\n\n"


def _summarize(node_name: str, delta: dict) -> str:
    if node_name == "classify_intent":
        return f"Detected intent: {delta.get('intent')} ({delta.get('intent_confidence', 0):.2f} confidence)"
    if node_name == "fetch_reddit":
        return f"Found {len(delta.get('posts', []))} relevant Reddit posts"
    if node_name == "analyze_sentiment":
        s = delta.get("sentiment")
        return f"Sentiment: {s.label} (avg {s.weighted_avg:.2f})" if s else "Sentiment analyzed"
    if node_name == "synthesize":
        return "Synthesized insight"
    if node_name == "fetch_company":
        cp = delta.get("company_profile")
        return f"Fetched profile for {cp.name}" if cp else "Fetched company profile"
    if node_name == "clarify":
        return "Needs clarification"
    return ""


def _start_turn(session_factory: sessionmaker[Session], session_id: str | None, message: str) -> str:
    with session_factory() as db:
        session = crud.get_or_create_session(db, session_id)
        crud.save_message(db, session.id, "user", message)
        return session.id


def _finish_turn(
    session_factory: sessionmaker[Session],
    session_id: str,
    content: str,
    intent: str,
    used_demo: bool,
) -> None:
    with session_factory() as db:
        crud.save_message(db, session_id, "assistant", content, intent=intent, used_demo_data=used_demo)


@router.post("/api/chat/stream")
async def chat_stream(payload: ChatRequest, bundle: GraphBundle = Depends(get_graph_bundle)):
    session_factory = get_session_factory()
    session_id = await run_in_threadpool(_start_turn, session_factory, payload.session_id, payload.message)

    async def event_stream():
        yield _sse({"type": "session", "session_id": session_id})
        yield _sse({"type": "step", "node": "classify_intent", "status": "started"})

        initial_state = {"session_id": session_id, "user_query": payload.message}
        final_intent = "unknown"
        final_demo_flags: dict[str, bool] = {}
        final_payload: dict = {}
        final_markdown = ""
        final_sentiment: dict = {}

        try:
            async for chunk in bundle.compiled.astream(initial_state, stream_mode="updates"):
                node_name, delta = next(iter(chunk.items()))

                flag_key = NODE_TO_FLAG_KEY.get(node_name)
                used_demo = bool(delta.get("demo_flags", {}).get(flag_key, False)) if flag_key else False

                yield _sse(
                    {
                        "type": "step",
                        "node": node_name,
                        "status": "completed",
                        "used_demo": used_demo,
                        "summary": _summarize(node_name, delta),
                    }
                )
                if used_demo:
                    yield _sse(
                        {"type": "error", "node": node_name, "message": f"{node_name} used sample/demo data"}
                    )

                if "demo_flags" in delta:
                    final_demo_flags = delta["demo_flags"]

                if node_name == "classify_intent":
                    final_intent = delta.get("intent", "unknown")
                    next_node = ROUTE_FROM_INTENT.get(final_intent, "clarify")
                    yield _sse({"type": "step", "node": next_node, "status": "started"})
                elif node_name in NEXT_NODE:
                    yield _sse({"type": "step", "node": NEXT_NODE[node_name], "status": "started"})
                    if node_name == "analyze_sentiment":
                        final_sentiment = delta["sentiment"].model_dump()
                elif node_name == "synthesize":
                    final_payload = {**delta["synthesis"].model_dump(), "sentiment": final_sentiment}
                    final_markdown = delta["synthesis"].headline
                elif node_name == "fetch_company":
                    profile = delta["company_profile"]
                    final_payload = profile.model_dump()
                    final_markdown = f"{profile.name}: {profile.description or 'No description available.'}"
                elif node_name == "clarify":
                    final_markdown = delta.get("final_response_markdown", "")
                    final_payload = {"message": final_markdown}
        except Exception as exc:
            logger.exception("graph execution failed")
            yield _sse({"type": "error", "node": "graph", "message": str(exc)})
            final_markdown = "Something went wrong processing your request."

        yield _sse(
            {"type": "result", "intent": final_intent, "payload": final_payload, "demo_flags": final_demo_flags}
        )

        await run_in_threadpool(
            _finish_turn,
            session_factory,
            session_id,
            final_markdown,
            final_intent,
            any(final_demo_flags.values()),
        )

        yield _sse({"type": "done"})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/api/chat/sessions/{session_id}/history", response_model=ChatHistoryResponse)
def get_history(session_id: str, db: Session = Depends(get_session)):
    messages = crud.get_history(db, session_id)
    return ChatHistoryResponse(
        session_id=session_id,
        messages=[
            ChatMessageOut(
                role=m.role,
                content=m.content,
                intent=m.intent,
                used_demo_data=m.used_demo_data,
                created_at=m.created_at.isoformat(),
            )
            for m in messages
        ],
    )
