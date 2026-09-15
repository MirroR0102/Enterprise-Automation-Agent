from langchain_core.tools import tool

from app.config import get_settings


def tavily_search(query: str) -> str:
    settings = get_settings()
    if not settings.tavily_api_key:
        return "搜索失败：未配置 TAVILY_API_KEY。请在 .env 中填写后再试。"
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Tavily 依赖不可用: {exc}") from exc
    tool_impl = TavilySearchResults(max_results=5, tavily_api_key=settings.tavily_api_key)
    try:
        result = tool_impl.invoke(query)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Tavily 搜索失败: {exc}") from exc
    if isinstance(result, str):
        return result
    import json

    return json.dumps(result, ensure_ascii=False, default=str)


@tool
def web_search(query: str) -> str:
    """使用 Tavily 搜索公开互联网信息，例如行业新闻。需要 TAVILY_API_KEY。"""
    return tavily_search(query)
