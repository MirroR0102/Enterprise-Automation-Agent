from datetime import datetime

from langchain_core.tools import tool


def get_current_time() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


@tool
def current_time() -> str:
    """返回当前本地时间（ISO-8601）。写周报时用于标注统计截止时间。"""
    return get_current_time()
