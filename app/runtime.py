"""进程内运行时状态：会话记录与跨线程取消标志。"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

_lock = threading.Lock()
# session_id → 是否已请求取消（供 Agent 节点轮询）
_flags: dict[str, bool] = {}


def set_cancelled(session_id: str, value: bool = True) -> None:
    """设置会话取消标志。"""
    with _lock:
        _flags[session_id] = value


def is_cancelled(session_id: str) -> bool:
    """查询会话是否已被取消。"""
    with _lock:
        return bool(_flags.get(session_id))


def clear_cancelled(session_id: str) -> None:
    """新任务开始前清除取消标志。"""
    with _lock:
        _flags.pop(session_id, None)


@dataclass
class SessionRecord:
    """内存中的对话会话：事件缓冲、状态与后台 asyncio.Task 引用。"""

    session_id: str
    user_id: int
    status: str = "idle"
    events: list[dict] = field(default_factory=list)
    task: object | None = None


_sessions: dict[str, SessionRecord] = {}


def create_session(session_id: str, user_id: int) -> SessionRecord:
    """注册新会话并返回 SessionRecord。"""
    rec = SessionRecord(session_id=session_id, user_id=user_id)
    with _lock:
        _sessions[session_id] = rec
    return rec


def get_session(session_id: str) -> SessionRecord | None:
    """按 session_id 查找会话。"""
    with _lock:
        return _sessions.get(session_id)


def list_sessions_for_user(user_id: int) -> list[SessionRecord]:
    """列出某用户的全部内存会话。"""
    with _lock:
        return [s for s in _sessions.values() if s.user_id == user_id]
