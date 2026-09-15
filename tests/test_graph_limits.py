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
    monkeypatch.setenv("MAX_TOOL_ROUNDS", "0")
    get_settings.cache_clear()
    graph = build_graph(llm=LoopLLM(), tools=[echo_tool])
    result = graph.invoke(
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
    assert result["status"] == "max_rounds"
    get_settings.cache_clear()


def test_tool_failure_retries_once_then_stops():
    graph = build_graph(llm=FailLLM(), tools=[boom])
    result = graph.invoke(
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
    assert result["status"] == "failed"
    errors = [e for e in result["events"] if e["type"] == "error"]
    assert errors
