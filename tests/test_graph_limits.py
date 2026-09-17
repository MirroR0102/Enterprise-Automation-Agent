"""LangGraph 编排限制：最大工具轮次与工具失败重试后停止。"""

import asyncio

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool

from app.agent.graph import build_graph
from app.config import get_settings


class LoopLLM:
    def __init__(self):
        self.n = 0

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        self.n += 1
        return AIMessage(
            content="继续调用工具",
            tool_calls=[{"name": "echo_tool", "args": {"text": "x"}, "id": f"call-{self.n}"}],
        )


class FailLLM:
    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        return AIMessage(
            content="调用会失败的工具",
            tool_calls=[{"name": "boom", "args": {"x": "1"}, "id": "call-fail"}],
        )


@tool
def echo_tool(text: str) -> str:
    """Echo for tests."""
    return text


@tool
def boom(x: str) -> str:
    """Always raise."""
    raise RuntimeError("boom")


def test_max_rounds_stops(monkeypatch):
    """MAX_TOOL_ROUNDS=0 时图应以 max_rounds 状态结束。"""
    monkeypatch.setenv("MAX_TOOL_ROUNDS", "0")
    get_settings.cache_clear()
    graph = build_graph(llm=LoopLLM(), tools=[echo_tool])
    result = asyncio.run(
        graph.ainvoke(
            {
                "messages": [HumanMessage(content="loop")],
                "session_id": "s-max",
                "user_id": 1,
                "tool_round": 0,
                "status": "running",
                "events": [],
            },
            {"configurable": {"thread_id": "s-max"}},
        )
    )
    assert result["status"] == "max_rounds"
    get_settings.cache_clear()


def test_tool_failure_retries_once_then_stops():
    """工具连续失败后 status=failed 且 events 含 error。"""
    graph = build_graph(llm=FailLLM(), tools=[boom])
    result = asyncio.run(
        graph.ainvoke(
            {
                "messages": [HumanMessage(content="fail")],
                "session_id": "s-fail",
                "user_id": 1,
                "tool_round": 0,
                "status": "running",
                "events": [],
            },
            {"configurable": {"thread_id": "s-fail"}},
        )
    )
    assert result["status"] == "failed"
    assert any(e.get("type") == "error" for e in result.get("events") or [])
