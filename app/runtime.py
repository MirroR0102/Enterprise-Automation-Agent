from __future__ import annotations

import threading
from dataclasses import dataclass, field

_lock = threading.Lock()
_flags: dict[str, bool] = {}


def set_cancelled(session_id: str, value: bool = True) -> None:
    with _lock:
        _flags[session_id] = value


def is_cancelled(session_id: str) -> bool:
    with _lock:
        return bool(_flags.get(session_id))


def clear_cancelled(session_id: str) -> None:
    with _lock:
        _flags.pop(session_id, None)


@dataclass
class SessionRecord:
    session_id: str
    user_id: int
    status: str = "idle"
    events: list[dict] = field(default_factory=list)
    task: object | None = None


_sessions: dict[str, SessionRecord] = {}


def create_session(session_id: str, user_id: int) -> SessionRecord:
    rec = SessionRecord(session_id=session_id, user_id=user_id)
    with _lock:
        _sessions[session_id] = rec
    return rec


def get_session(session_id: str) -> SessionRecord | None:
    with _lock:
        return _sessions.get(session_id)


def list_sessions_for_user(user_id: int) -> list[SessionRecord]:
    with _lock:
        return [s for s in _sessions.values() if s.user_id == user_id]
