from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

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


@pytest.fixture(autouse=True)
def override_auth():
    from app.auth import require_auth
    from app.main import app

    app.dependency_overrides[require_auth] = lambda: {"sub": "test-user"}
    yield
    app.dependency_overrides.pop(require_auth, None)


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
        await client.post("/chat", json={"question": "How many?", "session_id": "t3"})

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
        await client.post("/chat", json={"question": "Follow-up", "session_id": "t4"})

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
    assert response.status_code == 200
