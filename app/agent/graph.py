"""LangGraph 智能体图：定义 agent → tools → finalize 的状态流转与条件路由。"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agent.nodes import build_agent_node, build_tools_node, finalize_node
from app.agent.state import AgentState
from app.tools.registry import get_all_tools

_GRAPH = None
_CHECKPOINTER = MemorySaver()


def _route_after_agent(state: AgentState) -> str:
    """agent 节点执行后：异常终态直接结束，有 tool_calls 则进 tools，否则 finalize。"""
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
    """tools 节点执行后：异常终态结束，否则回到 agent 继续推理。"""
    status = state.get("status")
    if status in {"cancelled", "failed", "timeout", "max_rounds"}:
        return "end"
    return "agent"


def build_graph(llm=None, tools=None, checkpointer=None):
    """构建并编译 LangGraph 工作流；可注入 LLM、工具集与 checkpoint 存储。"""
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
    """返回进程内单例编译图，首次调用时懒加载。"""
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph(checkpointer=_CHECKPOINTER)
    return _GRAPH


def reset_graph_for_tests() -> None:
    """测试用：清空单例，强制下次重新 build。"""
    global _GRAPH
    _GRAPH = None
