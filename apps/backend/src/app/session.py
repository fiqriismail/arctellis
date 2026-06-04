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
