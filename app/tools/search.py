"""互联网搜索工具：基于 Tavily API，默认仅检索近一周新闻，禁止编造。"""

from __future__ import annotations

import json

from langchain_core.tools import tool

from app.config import get_settings


def tavily_search(query: str) -> str:
    """调用 Tavily：topic=news、time_range=week，仅返回近一周公开结果。"""
    settings = get_settings()
    if not settings.tavily_api_key:
        return (
            "搜索失败：未配置 TAVILY_API_KEY。请在 .env 中填写后再试。"
            "不得编造任何新闻标题、摘要或出处。"
        )
    try:
        from tavily import TavilyClient
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Tavily 依赖不可用: {exc}") from exc

    client = TavilyClient(api_key=settings.tavily_api_key)
    try:
        # time_range=week + topic=news：把结果限制在最近约 7 天的新闻域
        raw = client.search(
            query=query,
            topic="news",
            time_range="week",
            days=7,
            max_results=5,
            include_answer=False,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Tavily 搜索失败: {exc}") from exc

    results = raw.get("results") if isinstance(raw, dict) else None
    if not results:
        return (
            "未检索到近一周内的公开新闻结果。"
            "请在周报中明确写「本周未检索到公开新闻」，严禁编造新闻内容或虚假出处。"
        )

    slim = []
    for item in results:
        if not isinstance(item, dict):
            continue
        slim.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "published_date": item.get("published_date") or item.get("published_time"),
                "content": item.get("content") or item.get("snippet"),
            }
        )
    payload = {
        "scope": "past_7_days_news_only",
        "note": "仅含近一周公开检索结果；若列表为空或与主题无关，不得编造补充。",
        "results": slim,
    }
    return json.dumps(payload, ensure_ascii=False, default=str)


@tool
def web_search(query: str) -> str:
    """搜索近一周（past week）公开行业新闻。

    硬约束：
    - 检索范围固定为最近约 7 天（Tavily time_range=week / days=7），不要用它查全年旧闻；
    - 只许基于工具返回的标题/摘要/链接写新闻段落；
    - 无结果或失败时必须说明「本周未检索到」，严禁编造新闻事实、数据或出处。
    需要 TAVILY_API_KEY。
    """
    return tavily_search(query)
