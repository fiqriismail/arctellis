# BE-06 Conversation Endpoint + SSE Streaming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `POST /chat` endpoint that streams the agent's answer token-by-token via SSE and maintains per-session conversation history.

**Architecture:** `session.py` holds an in-memory dict (session_id → message list). `routers/chat.py` accepts `{question, session_id}`, prepends history to the messages, calls `agent.astream_events()`, and yields SSE events for each token. `main.py` gains a lifespan that builds the agent at startup and stores it on `app.state`. Tests set `app.state.agent` directly — `ASGITransport` (httpx 0.28) does not trigger the lifespan so the real SharePoint/OpenAI connections are never made in unit tests.

**Tech Stack:** Python 3.13 · FastAPI · `httpx.AsyncClient` + `ASGITransport` (testing) · pytest-asyncio · uv

**Story:** BE-06
**Working directory:** `apps/backend/` inside repo root `/Users/fiqriismail/Projects/Arctellis/group-one-rtp`

**Existing context:**
- `src/app/main.py` — bare FastAPI app with `/health`, no lifespan yet
- `src/app/agent.py` — `build_agent(service, settings)`, `invoke_agent(agent, question, history=None)`
- `src/app/config.py` — `get_settings()` (lru_cache)
- `src/app/services/graph_auth.py` — `GraphAuthService`
- `src/app/services/sharepoint.py` — `create_sharepoint_service(auth_service, settings)`
- `langchain_core.messages.AIMessageChunk` — has `.content: str` attribute
- `agent.astream_events({"messages": [...]}, version="v2")` — async generator yielding dicts with `event` key

---

## File Map

```
apps/backend/
├── src/app/
│   ├── main.py                ← add lifespan + include chat router (modify)
│   ├── session.py             ← in-memory session history (create)
│   └── routers/
│       ├── __init__.py        ← empty package marker (create)
│       └── chat.py            ← POST /chat + get_agent dependency + SSE (create)
└── tests/
    └── test_chat.py           ← unit tests — no real OpenAI/SharePoint (create)
```

---

## Task 1: Git branch

- [ ] **Step 1.1: Create feature branch**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git checkout -b feature/BE-06-conversation-endpoint
```

Expected: `Switched to a new branch 'feature/BE-06-conversation-endpoint'`

---

## Task 2: `session.py` — in-memory history store (TDD)

**Files:**
- Create: `apps/backend/src/app/session.py`
- Create: `apps/backend/tests/test_chat.py`

- [ ] **Step 2.1: Create the test file with session tests**

Create `apps/backend/tests/test_chat.py`:

```python
import pytest


# ── session store ─────────────────────────────────────────────────────────────

def setup_function():
    from app.session import reset_all
    reset_all()


def test_get_history_returns_empty_for_unknown_session():
    from app.session import get_history

    assert get_history("unknown") == []


def test_append_and_get_history():
    from app.session import append_to_history, get_history

    append_to_history("s1", "user", "Hello")
    history = get_history("s1")

    assert len(history) == 1
    assert history[0] == {"role": "user", "content": "Hello"}


def test_history_preserves_order():
    from app.session import append_to_history, get_history

    append_to_history("s2", "user", "Question")
    append_to_history("s2", "assistant", "Answer")
    history = get_history("s2")

    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"


def test_different_sessions_are_independent():
    from app.session import append_to_history, get_history

    append_to_history("alice", "user", "Hi from Alice")
    append_to_history("bob", "user", "Hi from Bob")

    assert get_history("alice")[0]["content"] == "Hi from Alice"
    assert get_history("bob")[0]["content"] == "Hi from Bob"
    assert len(get_history("alice")) == 1
    assert len(get_history("bob")) == 1


def test_clear_session_removes_history():
    from app.session import append_to_history, clear_session, get_history

    append_to_history("s3", "user", "To be cleared")
    clear_session("s3")

    assert get_history("s3") == []
```

- [ ] **Step 2.2: Run — verify FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_chat.py::test_get_history_returns_empty_for_unknown_session -v
```

Expected: `ModuleNotFoundError: No module named 'app.session'`

- [ ] **Step 2.3: Create `apps/backend/src/app/session.py`**

```python
from __future__ import annotations

from typing import Any

_sessions: dict[str, list[dict[str, Any]]] = {}


def get_history(session_id: str) -> list[dict[str, Any]]:
    """Return the message history for a session (empty list if unknown)."""
    return _sessions.get(session_id, [])


def append_to_history(session_id: str, role: str, content: str) -> None:
    """Append a message to a session's history."""
    if session_id not in _sessions:
        _sessions[session_id] = []
    _sessions[session_id].append({"role": role, "content": content})


def clear_session(session_id: str) -> None:
    """Remove all history for a session."""
    _sessions.pop(session_id, None)


def reset_all() -> None:
    """Clear all sessions. Use in tests only."""
    _sessions.clear()
```

- [ ] **Step 2.4: Run — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_chat.py -v
```

Expected: 5 passed.

- [ ] **Step 2.5: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/session.py apps/backend/tests/test_chat.py
git commit -m "feat(backend): add in-memory session history store (BE-06)"
```

---

## Task 3: `routers/chat.py` — POST /chat with SSE streaming (TDD)

**Files:**
- Create: `apps/backend/src/app/routers/__init__.py`
- Create: `apps/backend/src/app/routers/chat.py`
- Modify: `apps/backend/tests/test_chat.py`

**Key fact:** `httpx.AsyncClient(transport=ASGITransport(app=app))` does NOT trigger the FastAPI lifespan. Tests set `app.state.agent = mock_agent` directly.

- [ ] **Step 3.1: Create the package marker**

Create `apps/backend/src/app/routers/__init__.py` as an empty file.

- [ ] **Step 3.2: Create `apps/backend/src/app/routers/chat.py`**

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from app.session import append_to_history, get_history

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    session_id: str


async def get_agent(request: Request) -> CompiledStateGraph:
    return request.app.state.agent


@router.post("/chat")
async def chat(
    body: ChatRequest, agent: CompiledStateGraph = Depends(get_agent)
) -> StreamingResponse:
    history = get_history(body.session_id)
    messages = history + [{"role": "user", "content": body.question}]
    append_to_history(body.session_id, "user", body.question)

    async def event_stream():
        full_response: list[str] = []
        try:
            async for event in agent.astream_events(
                {"messages": messages}, version="v2"
            ):
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        token = chunk.content
                        full_response.append(token)
                        yield f"data: {token}\n\n"
            append_to_history(body.session_id, "assistant", "".join(full_response))
            yield "data: [DONE]\n\n"
        except Exception:
            yield "data: [ERROR] An error occurred. Please try again.\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

- [ ] **Step 3.3: Include the router in `apps/backend/src/app/main.py`**

Replace the entire content of `main.py` with:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.agent import build_agent
from app.config import get_settings
from app.routers.chat import router as chat_router
from app.services.graph_auth import GraphAuthService
from app.services.sharepoint import create_sharepoint_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not hasattr(app.state, "agent"):
        settings = get_settings()
        auth = GraphAuthService(
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id,
            client_secret=settings.azure_client_secret,
        )
        service = await create_sharepoint_service(auth_service=auth, settings=settings)
        app.state.agent = build_agent(service, settings)
    yield


app = FastAPI(
    title="Group One RTP Backend", version="0.1.0", lifespan=lifespan
)
app.include_router(chat_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 3.4: Append failing tests for the chat endpoint**

Append to the end of `apps/backend/tests/test_chat.py`:

```python
import pytest
from unittest.mock import MagicMock
from httpx import AsyncClient, ASGITransport


def _make_mock_agent(*tokens: str):
    """Return a mock agent that streams the given tokens."""
    mock = MagicMock()

    async def astream_events(input_data, **kwargs):
        for token in tokens:
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": MagicMock(content=token)},
            }
        yield {"event": "on_chain_end", "data": {}}

    mock.astream_events = astream_events
    return mock


# ── /chat endpoint ─────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_sessions():
    from app.session import reset_all
    reset_all()
    yield
    reset_all()


@pytest.mark.asyncio
async def test_chat_returns_sse_content_type():
    from app.main import app

    app.state.agent = _make_mock_agent("Hi")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/chat", json={"question": "hello", "session_id": "t1"}
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_chat_streams_tokens_in_sse_format():
    from app.main import app

    app.state.agent = _make_mock_agent("The ", "answer ", "is 42.")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/chat", json={"question": "What is it?", "session_id": "t2"}
        )

    assert "data: The \n\n" in response.text
    assert "data: answer \n\n" in response.text
    assert "data: is 42.\n\n" in response.text
    assert "data: [DONE]\n\n" in response.text


@pytest.mark.asyncio
async def test_chat_persists_history_after_response():
    from app.main import app
    from app.session import get_history

    app.state.agent = _make_mock_agent("42 items")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            "/chat", json={"question": "How many?", "session_id": "t3"}
        )

    history = get_history("t3")
    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "How many?"}
    assert history[1] == {"role": "assistant", "content": "42 items"}


@pytest.mark.asyncio
async def test_chat_second_question_receives_history():
    from app.main import app

    received_messages: list = []

    mock = MagicMock()

    async def astream_events(input_data, **kwargs):
        received_messages.append(input_data["messages"])
        yield {"event": "on_chain_end", "data": {}}

    mock.astream_events = astream_events
    app.state.agent = mock

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            "/chat", json={"question": "First question", "session_id": "t4"}
        )
        await client.post(
            "/chat", json={"question": "Follow-up", "session_id": "t4"}
        )

    # Second call should have the first exchange in its messages
    second_call_messages = received_messages[1]
    contents = [m["content"] for m in second_call_messages]
    assert "First question" in contents


@pytest.mark.asyncio
async def test_chat_agent_error_returns_error_event():
    from app.main import app

    mock = MagicMock()

    async def astream_events(input_data, **kwargs):
        raise RuntimeError("OpenAI connection failed")
        yield  # make it a generator

    mock.astream_events = astream_events
    app.state.agent = mock

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/chat", json={"question": "crash?", "session_id": "t5"}
        )

    assert "data: [ERROR]" in response.text
    assert response.status_code == 200  # SSE error, not HTTP error
```

- [ ] **Step 3.5: Run all tests — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_chat.py -v
```

Expected: 10 passed (5 session + 5 endpoint).

- [ ] **Step 3.6: Run full suite to confirm no regressions**

```bash
uv run pytest -q --tb=short
```

Expected: all tests pass.

- [ ] **Step 3.7: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/routers/ apps/backend/src/app/session.py \
        apps/backend/src/app/main.py apps/backend/tests/test_chat.py
git commit -m "feat(backend): add POST /chat SSE endpoint with session history (BE-06)"
```

---

## Task 4: Ruff lint + push

- [ ] **Step 4.1: Run ruff**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

Fix any issues:

```bash
uv run ruff format src/ tests/
uv run ruff check --fix src/ tests/
```

- [ ] **Step 4.2: Commit fixes if any**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/ apps/backend/tests/
git diff --staged --quiet || git commit -m "style(backend): ruff formatting (BE-06)"
```

- [ ] **Step 4.3: Final test run**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest -v
```

All tests must pass.

- [ ] **Step 4.4: Push**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git push -u origin feature/BE-06-conversation-endpoint
```

---

## Self-Review

**Spec coverage:**

| Acceptance criterion | Task |
|---|---|
| `POST /chat` accepts question + session ID (FR-4) | Task 3 |
| Per-session history maintained for follow-ups (FR-5) | Tasks 2 + 3: `session.py` + history prepended to messages |
| Streams tokens via SSE (FR-4) | Task 3: `astream_events` → `data: {token}\n\n` |
| Streaming verified with client consuming SSE | Task 3: `test_chat_streams_tokens_in_sse_format` |
| Errors surface cleanly without leaking internals | Task 3: `except Exception → data: [ERROR] An error occurred...` |

**Placeholder scan:** None found — all code is complete.

**Type consistency:**
- `session.py`: `get_history(session_id) -> list[dict[str, Any]]`, `append_to_history(session_id, role, content)`, `clear_session(session_id)`, `reset_all()` — consistent across Task 2 tests and Task 3 endpoint.
- `ChatRequest(question: str, session_id: str)` — consistent across Task 3 endpoint and all test `json=` payloads.
- `event_stream` yields `f"data: {token}\n\n"` and `"data: [DONE]\n\n"` — consistent with test assertions (`"data: The \n\n"`, `"data: [DONE]\n\n"`).
