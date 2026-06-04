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
