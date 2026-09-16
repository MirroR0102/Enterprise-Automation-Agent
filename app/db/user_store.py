"""Per-user storage for conversations and weekly reports (MySQL schema or SQLite file)."""

from __future__ import annotations

import json
import re
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from app.config import ROOT_DIR, get_settings
from app.db.mysql import parse_mysql_dsn

_lock = threading.RLock()
_sqlite_pool: dict[int, sqlite3.Connection] = {}

_SAFE = re.compile(r"^eoa_u_\d+$")


def user_schema_name(user_id: int) -> str:
    name = f"eoa_u_{int(user_id)}"
    if not _SAFE.match(name):
        raise ValueError("invalid user schema")
    return name


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _sqlite_path(user_id: int) -> Path:
    path = ROOT_DIR / "data" / "users" / f"u_{int(user_id)}.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _get_sqlite(user_id: int) -> sqlite3.Connection:
    with _lock:
        conn = _sqlite_pool.get(user_id)
        if conn is None:
            conn = sqlite3.connect(str(_sqlite_path(user_id)), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            _sqlite_pool[user_id] = conn
        return conn


def _mysql_connect(database: str | None = None):
    import pymysql

    parts = parse_mysql_dsn(get_settings().mysql_dsn)
    kwargs: dict[str, Any] = {
        "host": parts.host,
        "port": parts.port,
        "user": parts.user,
        "password": parts.password,
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": True,
    }
    if database:
        kwargs["database"] = database
    return pymysql.connect(**kwargs)


_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tool_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    event_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS weekly_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    title TEXT NOT NULL,
    markdown TEXT NOT NULL,
    file_relpath TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
"""


def ensure_user_store(user_id: int) -> None:
    settings = get_settings()
    if settings.use_mock_db:
        conn = _get_sqlite(user_id)
        conn.executescript(_SCHEMA_SQLITE)
        conn.commit()
        return

    schema = user_schema_name(user_id)
    root = _mysql_connect(database=None)
    try:
        with root.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{schema}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        root.close()

    conn = _mysql_connect(database=schema)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id VARCHAR(64) PRIMARY KEY,
                    title VARCHAR(255) NOT NULL DEFAULT '',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    conversation_id VARCHAR(64) NOT NULL,
                    role VARCHAR(32) NOT NULL,
                    content MEDIUMTEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_msg_conv (conversation_id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tool_events (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    conversation_id VARCHAR(64) NOT NULL,
                    event_json JSON NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_evt_conv (conversation_id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS weekly_reports (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    conversation_id VARCHAR(64) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    markdown MEDIUMTEXT NOT NULL,
                    file_relpath VARCHAR(512) NOT NULL DEFAULT '',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_rep_conv (conversation_id)
                )
                """
            )
    finally:
        conn.close()


@contextmanager
def user_connection(user_id: int) -> Iterator[Any]:
    ensure_user_store(user_id)
    settings = get_settings()
    if settings.use_mock_db:
        conn = _get_sqlite(user_id)
        yield conn
        conn.commit()
        return
    conn = _mysql_connect(database=user_schema_name(user_id))
    try:
        yield conn
    finally:
        conn.close()


def ensure_conversation(user_id: int, conversation_id: str, title: str = "") -> None:
    now = _utc_now()
    with user_connection(user_id) as conn:
        if get_settings().use_mock_db:
            row = conn.execute(
                "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (conversation_id, title or "新对话", now, now),
                )
            else:
                conn.execute(
                    "UPDATE conversations SET updated_at = ? WHERE id = ?",
                    (now, conversation_id),
                )
            return
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM conversations WHERE id = %s", (conversation_id,))
            if cur.fetchone() is None:
                cur.execute(
                    "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (%s, %s, %s, %s)",
                    (conversation_id, title or "新对话", now, now),
                )
            else:
                cur.execute(
                    "UPDATE conversations SET updated_at = %s WHERE id = %s",
                    (now, conversation_id),
                )


def add_message(user_id: int, conversation_id: str, role: str, content: str) -> None:
    ensure_conversation(user_id, conversation_id)
    now = _utc_now()
    with user_connection(user_id) as conn:
        if get_settings().use_mock_db:
            conn.execute(
                "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (conversation_id, role, content, now),
            )
            return
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (%s, %s, %s, %s)",
                (conversation_id, role, content, now),
            )


def add_tool_event(user_id: int, conversation_id: str, event: dict[str, Any]) -> None:
    ensure_conversation(user_id, conversation_id)
    now = _utc_now()
    blob = json.dumps(event, ensure_ascii=False, default=str)
    with user_connection(user_id) as conn:
        if get_settings().use_mock_db:
            conn.execute(
                "INSERT INTO tool_events (conversation_id, event_json, created_at) VALUES (?, ?, ?)",
                (conversation_id, blob, now),
            )
            return
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tool_events (conversation_id, event_json, created_at) VALUES (%s, %s, %s)",
                (conversation_id, blob, now),
            )


def save_weekly_report(
    user_id: int,
    conversation_id: str,
    markdown: str,
    title: str = "",
    file_relpath: str = "",
) -> int:
    ensure_conversation(user_id, conversation_id, title=title or "运营周报")
    now = _utc_now()
    title = title or _title_from_markdown(markdown)
    with user_connection(user_id) as conn:
        if get_settings().use_mock_db:
            cur = conn.execute(
                "INSERT INTO weekly_reports (conversation_id, title, markdown, file_relpath, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (conversation_id, title, markdown, file_relpath, now),
            )
            return int(cur.lastrowid)
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO weekly_reports (conversation_id, title, markdown, file_relpath, created_at) "
                "VALUES (%s, %s, %s, %s, %s)",
                (conversation_id, title, markdown, file_relpath, now),
            )
            return int(cur.lastrowid)


def list_weekly_reports(user_id: int, limit: int = 50) -> list[dict[str, Any]]:
    ensure_user_store(user_id)
    limit = max(1, min(int(limit), 200))
    with user_connection(user_id) as conn:
        if get_settings().use_mock_db:
            rows = conn.execute(
                "SELECT id, conversation_id, title, created_at, file_relpath "
                "FROM weekly_reports ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, conversation_id, title, created_at, file_relpath "
                "FROM weekly_reports ORDER BY id DESC LIMIT %s",
                (limit,),
            )
            return list(cur.fetchall() or [])


def get_weekly_report(user_id: int, report_id: int) -> dict[str, Any] | None:
    ensure_user_store(user_id)
    with user_connection(user_id) as conn:
        if get_settings().use_mock_db:
            row = conn.execute(
                "SELECT id, conversation_id, title, markdown, file_relpath, created_at "
                "FROM weekly_reports WHERE id = ?",
                (report_id,),
            ).fetchone()
            return dict(row) if row else None
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, conversation_id, title, markdown, file_relpath, created_at "
                "FROM weekly_reports WHERE id = %s",
                (report_id,),
            )
            return cur.fetchone()


def _title_from_markdown(markdown: str) -> str:
    for line in (markdown or "").splitlines():
        s = line.strip()
        if s.startswith("#"):
            return s.lstrip("#").strip()[:80] or "运营周报"
    return "运营周报"
