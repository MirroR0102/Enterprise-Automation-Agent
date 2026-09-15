from __future__ import annotations

import json
import re

from langchain_core.tools import tool

_FORBIDDEN = re.compile(
    r"\b(drop|alter|delete|truncate|insert|update|create|grant|revoke)\b",
    re.IGNORECASE,
)


def is_safe_select_sql(sql: str) -> bool:
    if sql is None:
        return False
    stripped = str(sql).strip()
    if not stripped:
        return False
    if ";" in stripped.rstrip(";"):
        return False
    core = stripped.rstrip(";").strip()
    if not re.match(r"^select\b", core, re.IGNORECASE):
        return False
    if _FORBIDDEN.search(core):
        return False
    return True


def run_mysql_query(sql: str) -> str:
    if not is_safe_select_sql(sql):
        return "拒绝执行：仅允许单条只读 SELECT，且不得包含写操作或高危关键字。"
    from app.db.mysql import execute_readonly_query

    try:
        rows = execute_readonly_query(sql.rstrip(";").strip())
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"查询执行失败: {exc}") from exc
    return json.dumps(rows, ensure_ascii=False, default=str)


@tool
def mysql_query(sql: str) -> str:
    """对业务库执行只读 SELECT。用于查询销售额等指标。禁止 DROP/DELETE/UPDATE 等写语句。"""
    return run_mysql_query(sql)
