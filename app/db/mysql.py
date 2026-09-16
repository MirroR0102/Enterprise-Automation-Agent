from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import unquote, urlparse

from app.config import ROOT_DIR, get_settings

_lock = threading.RLock()
_sqlite_conn: sqlite3.Connection | None = None


@dataclass
class MysqlParts:
    user: str
    password: str
    host: str
    port: int
    database: str


def parse_mysql_dsn(dsn: str) -> MysqlParts:
    raw = dsn
    if dsn.startswith("mysql+pymysql://"):
        raw = "mysql://" + dsn[len("mysql+pymysql://") :]
    parsed = urlparse(raw)
    if parsed.scheme not in {"mysql", "mysql+pymysql"}:
        raise ValueError(f"unsupported MYSQL_DSN scheme: {parsed.scheme}")
    database = (parsed.path or "").lstrip("/")
    if not database:
        raise ValueError("MYSQL_DSN must include a database name")
    return MysqlParts(
        user=unquote(parsed.username or "root"),
        password=unquote(parsed.password or ""),
        host=parsed.hostname or "127.0.0.1",
        port=parsed.port or 3306,
        database=database,
    )


def sqlite_path() -> Path:
    override = os.environ.get("MOCK_DB_PATH", "").strip()
    if override:
        path = Path(override)
    else:
        path = ROOT_DIR / "data" / "mock.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_sqlite() -> sqlite3.Connection:
    global _sqlite_conn
    with _lock:
        if _sqlite_conn is None:
            conn = sqlite3.connect(str(sqlite_path()), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            _sqlite_conn = conn
        return _sqlite_conn


def reset_sqlite_for_tests() -> None:
    global _sqlite_conn
    with _lock:
        if _sqlite_conn is not None:
            _sqlite_conn.close()
            _sqlite_conn = None
        path = sqlite_path()
        if path.exists():
            try:
                path.unlink()
            except PermissionError:
                # Another process may hold the file; fall back to truncating tables.
                conn = sqlite3.connect(str(path), check_same_thread=False)
                try:
                    conn.executescript(
                        "DROP TABLE IF EXISTS agent_logs;"
                        "DROP TABLE IF EXISTS sales;"
                        "DROP TABLE IF EXISTS users;"
                    )
                    conn.commit()
                finally:
                    conn.close()


def _mysql_connect(database: str | None = ...):  # type: ignore[assignment]
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
    if database is ...:
        kwargs["database"] = parts.database
    elif database:
        kwargs["database"] = database
    return pymysql.connect(**kwargs)


@contextmanager
def get_connection() -> Iterator[Any]:
    settings = get_settings()
    if settings.use_mock_db:
        conn = get_sqlite()
        yield conn
        conn.commit()
        return
    conn = _mysql_connect()
    try:
        yield conn
    finally:
        conn.close()


def init_schema_and_seed() -> None:
    from app.auth.security import hash_password

    settings = get_settings()
    if settings.use_mock_db:
        _init_sqlite(hash_password)
        return
    _init_mysql(hash_password)


def _init_sqlite(hash_password) -> None:
    conn = get_sqlite()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_date TEXT NOT NULL,
            amount REAL NOT NULL,
            region TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS agent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_id INTEGER,
            event_type TEXT NOT NULL,
            content_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_agent_logs_session ON agent_logs(session_id);
        CREATE INDEX IF NOT EXISTS idx_agent_logs_created ON agent_logs(created_at);
        """
    )
    _seed_users(conn, hash_password)
    if conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO sales (sale_date, amount, region) VALUES (?, ?, ?)",
            _sales_rows(),
        )
    conn.commit()


def _init_mysql(hash_password) -> None:
    parts = parse_mysql_dsn(get_settings().mysql_dsn)
    root = _mysql_connect(database=None)
    try:
        with root.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{parts.database}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        root.close()

    conn = _mysql_connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(64) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(16) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sales (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    sale_date DATE NOT NULL,
                    amount DECIMAL(12, 2) NOT NULL,
                    region VARCHAR(64) NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_logs (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    session_id VARCHAR(64) NOT NULL,
                    user_id INT NULL,
                    event_type VARCHAR(32) NOT NULL,
                    content_json JSON NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_agent_logs_session (session_id),
                    INDEX idx_agent_logs_created (created_at)
                )
                """
            )
            _seed_users_mysql(cur, hash_password)
            cur.execute("SELECT COUNT(*) AS c FROM sales")
            row = cur.fetchone()
            count = row["c"] if isinstance(row, dict) else row[0]
            if count == 0:
                cur.executemany(
                    "INSERT INTO sales (sale_date, amount, region) VALUES (%s, %s, %s)",
                    _sales_rows(),
                )
    finally:
        conn.close()


def _sales_rows() -> list[tuple]:
    return [
        ("2026-09-01", 20000.00, "华东"),
        ("2026-09-05", 35000.00, "华北"),
        ("2026-09-10", 45000.00, "华南"),
        ("2025-09-03", 18000.00, "华东"),
        ("2025-09-12", 22000.00, "华北"),
        ("2025-09-20", 40000.00, "华南"),
        ("2026-08-15", 12000.00, "西南"),
    ]


def _seed_users(conn: sqlite3.Connection, hash_password) -> None:
    settings = get_settings()
    for username, password, role in (
        (settings.demo_ops_username, settings.demo_ops_password, "ops"),
        (settings.demo_dev_username, settings.demo_dev_password, "dev"),
    ):
        row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, hash_password(password), role),
            )


def _seed_users_mysql(cur, hash_password) -> None:
    settings = get_settings()
    for username, password, role in (
        (settings.demo_ops_username, settings.demo_ops_password, "ops"),
        (settings.demo_dev_username, settings.demo_dev_password, "dev"),
    ):
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (username, hash_password(password), role),
            )


def fetch_user_by_username(username: str) -> dict | None:
    with get_connection() as conn:
        if get_settings().use_mock_db:
            row = conn.execute(
                "SELECT id, username, password_hash, role FROM users WHERE username = ?",
                (username,),
            ).fetchone()
            return dict(row) if row else None
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, password_hash, role FROM users WHERE username = %s",
                (username,),
            )
            return cur.fetchone()


def fetch_user_by_id(user_id: int) -> dict | None:
    with get_connection() as conn:
        if get_settings().use_mock_db:
            row = conn.execute(
                "SELECT id, username, password_hash, role FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            return dict(row) if row else None
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, password_hash, role FROM users WHERE id = %s",
                (user_id,),
            )
            return cur.fetchone()


def execute_readonly_query(sql: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if get_settings().use_mock_db:
            cur = conn.execute(sql)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return list(rows or [])
