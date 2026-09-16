"""当前时间工具：供 Agent 标注统计截止时间。"""

from datetime import datetime

from langchain_core.tools import tool


def get_current_time() -> str:
    """返回本地时区的 ISO-8601 时间字符串。"""
    return datetime.now().astimezone().isoformat(timespec="seconds")


@tool
def current_time() -> str:
    """返回当前本地时间（ISO-8601）。写周报时用于标注统计截止时间。"""
    return get_current_time()
