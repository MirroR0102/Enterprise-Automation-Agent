from __future__ import annotations

import json

from langchain_core.tools import tool

from app.tools.calculator import calculator
from app.tools.file_io import read_markdown_report, write_markdown_report
from app.tools.kb import query_enterprise_kb
from app.tools.mysql_query import mysql_query
from app.tools.search import web_search
from app.tools.time_tool import current_time


@tool
def enterprise_knowledge_search(question: str, top_k: int = 5) -> str:
    """查询企业内部知识库（规范、制度）。默认未接入时返回 stub，禁止把 stub 当真实资料写进周报。"""
    hit = query_enterprise_kb(question=question, top_k=top_k)
    payload = hit.as_dict()
    payload["stub"] = not hit.hit and payload.get("answer") == "当前未接入企业内部知识库"
    return json.dumps(payload, ensure_ascii=False)


def get_all_tools() -> list:
    return [
        web_search,
        calculator,
        current_time,
        mysql_query,
        write_markdown_report,
        read_markdown_report,
        enterprise_knowledge_search,
    ]
