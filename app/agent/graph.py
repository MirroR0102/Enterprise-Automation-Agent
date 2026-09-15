from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agent.nodes import build_agent_node, build_tools_node, finalize_node
from app.agent.state import AgentState
from app.tools.registry import get_all_tools

_GRAPH = None
_CHECKPOINTER = MemorySaver()


def _route_after_agent(state: AgentState) -> str:
    status = state.get("status")
    if status in {"cancelled", "failed", "timeout", "max_rounds"}:
        return "end"
    messages = state.get("messages") or []
    if not messages:
        return "finalize"
    last = messages[-1]
    tool_calls = getattr(last, "tool_calls", None) or []
    if tool_calls:
        return "tools"
    return "finalize"


def _route_after_tools(state: AgentState) -> str:
    status = state.get("status")
    if status in {"cancelled", "failed", "timeout", "max_rounds"}:
        return "end"
    return "agent"


def build_graph(llm=None, tools=None, checkpointer=None):
    tools = tools if tools is not None else get_all_tools()
    builder = StateGraph(AgentState)
    builder.add_node("agent", build_agent_node(llm=llm, tools=tools))
    builder.add_node("tools", build_tools_node(tools))
    builder.add_node("finalize", finalize_node)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        _route_after_agent,
        {"tools": "tools", "finalize": "finalize", "end": END},
    )
    builder.add_conditional_edges(
        "tools",
        _route_after_tools,
        {"agent": "agent", "end": END},
    )
    builder.add_edge("finalize", END)
    return builder.compile(checkpointer=checkpointer or MemorySaver())


def get_compiled_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph(checkpointer=_CHECKPOINTER)
    return _GRAPH


def reset_graph_for_tests() -> None:
    global _GRAPH
    _GRAPH = None
