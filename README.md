# Market Intelligence Chatbot

A market intelligence assistant for startup founders. Ask about a trend, gauge sentiment
around a topic, or pull up competitor data — a LangGraph agent pipeline routes the
question, fetches live data (Reddit, People Data Labs, Perplexity), and streams back a
structured, cited answer over Server-Sent Events to a Next.js chat UI.

## Architecture

```
Next.js (TypeScript, App Router)
   │  fetch + ReadableStream (SSE)
   ▼
FastAPI  ──►  LangGraph StateGraph
                 │
                 ├── classify_intent ──► routes on intent ──┬── fetch_reddit ─► analyze_sentiment ─► synthesize ─► END
                 │                                          ├── fetch_company ───────────────────────────────────► END
                 │                                          └── clarify (low confidence / unknown) ───────────────► END
                 │
        each node calls a service client (Perplexity / Reddit / PDL) with retry +
        automatic demo-data fallback, then writes typed updates onto shared graph state
```

- **Backend**: FastAPI + [LangGraph](https://langchain-ai.github.io/langgraph/) StateGraph, SQLite (session-scoped chat history), Pydantic schemas end to end.
- **Frontend**: Next.js (App Router) + TypeScript + Tailwind, consuming the backend's SSE stream directly with `fetch`/`ReadableStream`.
- **External services**: Perplexity (`sonar`, structured JSON output) for intent classification + synthesis, Reddit via `asyncpraw` for trend/sentiment source data, People Data Labs for company enrichment.

## Why these choices (interview notes)

- **SSE, not WebSockets.** The data flow is one-directional — the backend pushes step
  progress and a final result; the next user message is a new request, not a message on
  the same socket. SSE runs over plain HTTP (no upgrade handshake, works through any
  reverse proxy) and is natively readable via `fetch` + `ReadableStream` in the browser.
  `EventSource` was ruled out because it only supports GET, and sending the chat message
  requires a POST body.
- **Demo-fallback lives in the service-client layer, not the node layer.** Every client
  (`PerplexityClient`, `RedditClient`, `PDLClient`) exposes `is_configured()` and routes
  through one shared `call_with_fallback()` helper. A missing API key and a failed live
  call hit the exact same code path — a graph node never has to know *why* it got demo
  data, only that it did (`used_demo: bool`), and that flag propagates all the way to a
  visible amber badge in the UI. Nothing pretends to be live data silently.
- **Structured JSON output instead of substring-matching an LLM's free text.** Both intent
  classification and synthesis use Perplexity's `response_format: json_schema` and are
  validated through Pydantic before being trusted. A malformed or low-confidence response
  routes to a `clarify` node instead of guessing.
- **LangGraph node names are distinct from state field names** (`classify_intent` vs.
  `intent`, etc.) — LangGraph raises at graph-build time if a node id collides with a
  state key, so this isn't cosmetic.
- **Streaming progress is driven by `stream_mode="updates"`, not `get_stream_writer()`.**
  LangGraph's own docs flag that `get_stream_writer()` relies on contextvar propagation
  that isn't reliable across async tasks on Python < 3.11. Rather than pin a Python
  version around a streaming primitive, the FastAPI route reads `stream_mode="updates"`
  chunks (`{node_name: state_delta}` after each node completes) and synthesizes
  "started"/"completed" SSE events from the graph's known, deterministic routing table.
  Nodes stay pure functions of state — no side-channel writer calls.
- **Sync SQLAlchemy + `run_in_threadpool`, not `aiosqlite`.** `asyncpraw` pins
  `aiosqlite<=0.17.0` for its own internal cache; that version is incompatible with
  SQLAlchemy 2.x's async connection-termination path and crashes with an `AttributeError`
  the moment a request is cancelled mid-stream. Going sync for the app's own (tiny) SQLite
  usage sidesteps the conflict entirely instead of fighting a transitive pin.

## Project layout

```
backend/
  app/
    graph/            LangGraph state, nodes, routing
    services/          Perplexity/Reddit/PDL clients + demo-data fixtures
    schemas/            Pydantic models (shared by graph state and API responses)
    db/                  SQLAlchemy models, session-scoped chat history
    api/routers/          /api/chat/stream (SSE), /api/health
  tests/                 pytest, fully mocked, zero live network calls
frontend/
  app/                  Next.js App Router pages
  components/chat/       Chat window, input, agent step timeline, demo badge
  components/results/    Sentiment chart, synthesis card, company card
  lib/                   SSE client, types, session storage
  hooks/useChatStream.ts  Streaming state machine
docker-compose.yml
.env.example
```

## Local development

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements-dev.txt
cp ../.env.example .env       # fill in real keys, or leave blank to run in demo mode
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                    # http://localhost:3000
```

### With Docker Compose

```bash
cp .env.example backend/.env   # fill in real keys, or leave blank for demo mode
docker-compose up --build
```

Any key left blank in `.env` makes that service run in demo mode: the app stays fully
functional and every response that used sample data is visibly labeled, instead of
crashing.

## Running tests

```bash
cd backend && pytest                 # unit + integration, all mocked, no network calls
cd frontend && npm test               # Vitest: SSE parser, step-state reducer
cd frontend && npx tsc --noEmit       # typecheck
```

## API keys

| Service | Used for | Get a key |
|---|---|---|
| Perplexity | Intent classification, synthesis | https://www.perplexity.ai/settings/api |
| Reddit (`asyncpraw`) | Trend/sentiment source posts | https://www.reddit.com/prefs/apps |
| People Data Labs | Competitor/company enrichment | https://www.peopledatalabs.com/ |
| Crunchbase (optional) | Secondary company enrichment | Disabled by default (`ENABLE_CRUNCHBASE=false`) — no key required unless enabled |

## Known limitations

- The local heuristic intent classifier (`_local_heuristic_classify` in
  `intent_node.py`) only runs when Perplexity itself is unreachable — it's a
  deliberately crude last-resort fallback (keyword/stopword matching, not real NLP), not
  the primary accuracy story. The real classifier uses structured LLM output with
  few-shot examples.
- Crunchbase is disabled by default and unimplemented beyond a safe no-op stub
  (`services/crunchbase_client.py`) — no key was available to build and verify against.
- SQLite chat history is fine for a single-instance demo; it isn't set up for multi-instance
  deployment (no connection pooling across processes).
