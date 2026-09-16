"""Agent 事件日志：写入 MySQL/SQLite，DB 不可用时降级到内存。"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import get_settings
from app.db.mysql import get_connection

_memory_logs: list[dict[str, Any]] = []


def log_event(
    session_id: str,
    event_type: str,
    payload: dict[str, Any],
    user_id: int | None = None,
) -> None:
    """持久化单条事件；失败时追加到进程内 _memory_logs。"""
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    body = dict(payload)
    body.setdefault("type", event_type)
    record = {
        "session_id": session_id,
        "user_id": user_id,
        "event_type": event_type,
        "content_json": body,
        "created_at": created_at,
    }
    settings = get_settings()
    try:
        with get_connection() as conn:
            blob = json.dumps(body, ensure_ascii=False, default=str)
            if settings.use_mock_db:
                conn.execute(
                    "INSERT INTO agent_logs (session_id, user_id, event_type, content_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (session_id, user_id, event_type, blob, created_at),
                )
            else:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO agent_logs (session_id, user_id, event_type, content_json, created_at) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (session_id, user_id, event_type, blob, created_at),
                    )
    except Exception:
        _memory_logs.append(record)


def _row_to_event(row: dict[str, Any]) -> dict[str, Any]:
    """将 DB 行转为前端/SSE 兼容的事件 dict。"""
    content = row.get("content_json")
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except json.JSONDecodeError:
            content = {"content": content}
    event = dict(content or {})
    event.setdefault("type", row.get("event_type"))
    event.setdefault("timestamp", row.get("created_at"))
    event["session_id"] = row.get("session_id")
    event["user_id"] = row.get("user_id")
    return event


def list_events(session_id: str) -> list[dict[str, Any]]:
    """按 session_id 升序返回全部事件。"""
    settings = get_settings()
    try:
        with get_connection() as conn:
            if settings.use_mock_db:
                rows = conn.execute(
                    "SELECT session_id, user_id, event_type, content_json, created_at "
                    "FROM agent_logs WHERE session_id = ? ORDER BY id ASC",
                    (session_id,),
                ).fetchall()
                return [_row_to_event(dict(r)) for r in rows]
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT session_id, user_id, event_type, content_json, created_at "
                    "FROM agent_logs WHERE session_id = %s ORDER BY id ASC",
                    (session_id,),
                )
                return [_row_to_event(dict(r)) for r in cur.fetchall()]
    except Exception:
        return [r for r in _memory_logs if r["session_id"] == session_id]


def list_recent(limit: int = 100, session_id: str | None = None) -> list[dict[str, Any]]:
    """查询最近 N 条日志，供 dev 运维接口使用。"""
    settings = get_settings()
    limit = max(1, min(int(limit), 500))
    try:
        with get_connection() as conn:
            if settings.use_mock_db:
                if session_id:
                    rows = conn.execute(
                        "SELECT session_id, user_id, event_type, content_json, created_at "
                        "FROM agent_logs WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                        (session_id, limit),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT session_id, user_id, event_type, content_json, created_at "
                        "FROM agent_logs ORDER BY id DESC LIMIT ?",
                        (limit,),
                    ).fetchall()
                return [_row_to_event(dict(r)) for r in rows]
            with conn.cursor() as cur:
                if session_id:
                    cur.execute(
                        "SELECT session_id, user_id, event_type, content_json, created_at "
                        "FROM agent_logs WHERE session_id = %s ORDER BY id DESC LIMIT %s",
                        (session_id, limit),
                    )
                else:
                    cur.execute(
                        "SELECT session_id, user_id, event_type, content_json, created_at "
                        "FROM agent_logs ORDER BY id DESC LIMIT %s",
                        (limit,),
                    )
                return [_row_to_event(dict(r)) for r in cur.fetchall()]
    except Exception:
        items = list(_memory_logs)
        if session_id:
            items = [r for r in items if r["session_id"] == session_id]
        return list(reversed(items[-limit:]))


def purge_old_logs(days: int | None = None) -> int:
    """按保留天数清理过期日志，返回删除行数。"""
    settings = get_settings()
    days = settings.log_retention_days if days is None else days
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_s = cutoff.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with get_connection() as conn:
            if settings.use_mock_db:
                cur = conn.execute(
                    "DELETE FROM agent_logs WHERE created_at < ?",
                    (cutoff.isoformat(timespec="seconds"),),
                )
                return cur.rowcount or 0
            with conn.cursor() as cur:
                cur.execute("DELETE FROM agent_logs WHERE created_at < %s", (cutoff_s,))
                return cur.rowcount or 0
    except Exception:
        return 0
