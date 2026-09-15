from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langgraph.prebuilt import ToolNode

from app.agent.prompts import SYSTEM_PROMPT
from app.config import get_settings
from app.runtime import is_cancelled


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_event(
    event_type: str,
    content: str,
    *,
    tool: str | None = None,
    input: str | None = None,
    output: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": event_type,
        "timestamp": utc_now(),
        "content": content,
    }
    if tool is not None:
        payload["tool"] = tool
    if input is not None:
        payload["input"] = input
    if output is not None:
        payload["output"] = output
    return payload


def _append(events: list[dict[str, Any]] | None, item: dict[str, Any]) -> list[dict[str, Any]]:
    return list(events or []) + [item]


def _cancelled(state: dict) -> dict:
    event = make_event("cancelled", "任务已被人工终止")
    return {
        "status": "cancelled",
        "events": _append(state.get("events"), event),
    }


def _persist(state: dict, event: dict) -> None:
    from app.logging_service import log_event
    from app.runtime import get_session

    log_event(state.get("session_id") or "", event["type"], event, user_id=state.get("user_id"))
    rec = get_session(state.get("session_id") or "")
    if rec is not None:
        rec.events.append(event)
        if event.get("type") in {"cancelled", "failed", "timeout", "max_rounds", "final"}:
            mapping = {
                "cancelled": "cancelled",
                "failed": "failed",
                "timeout": "timeout",
                "max_rounds": "max_rounds",
                "final": "completed",
            }
            rec.status = mapping[event["type"]]


def get_llm(llm=None):
    if llm is not None:
        return llm
    from langchain_openai import ChatOpenAI

    settings = get_settings()
    provider = (settings.llm_provider or "deepseek").lower()
    if provider == "openai":
        return ChatOpenAI(
            model=settings.openai_model or "gpt-4o-mini",
            api_key=settings.openai_api_key or "missing",
            base_url=settings.openai_base_url,
            temperature=0,
        )
    if provider == "qwen":
        return ChatOpenAI(
            model=settings.qwen_model,
            api_key=settings.qwen_api_key or "missing",
            base_url=settings.qwen_base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            temperature=0,
        )
    return ChatOpenAI(
        model=settings.llm_model or "deepseek-chat",
        api_key=settings.deepseek_api_key or "missing",
        base_url=settings.deepseek_base_url,
        temperature=0,
    )


def build_agent_node(llm=None, tools=None):
    def agent_node(state: dict) -> dict:
        if is_cancelled(state.get("session_id") or ""):
            result = _cancelled(state)
            _persist(state, result["events"][-1])
            return result
        from langchain_core.messages import SystemMessage

        bound = get_llm(llm).bind_tools(tools or [])
        messages = [SystemMessage(content=SYSTEM_PROMPT), *state.get("messages", [])]
        response = bound.invoke(messages)
        events = list(state.get("events") or [])
        thought = getattr(response, "content", "") or ""
        if thought:
            event = make_event("thought", thought if isinstance(thought, str) else str(thought))
            events.append(event)
            _persist(state, event)
        return {"messages": [response], "events": events, "status": "running"}

    return agent_node


def build_tools_node(tools):
    try:
        inner = ToolNode(tools, handle_tool_errors=False)
    except TypeError:
        inner = ToolNode(tools)

    def tools_node(state: dict) -> dict:
        if is_cancelled(state.get("session_id") or ""):
            result = _cancelled(state)
            _persist(state, result["events"][-1])
            return result
        settings = get_settings()
        tool_round = int(state.get("tool_round") or 0) + 1
        events = list(state.get("events") or [])
        if tool_round > settings.max_tool_rounds:
            event = make_event(
                "max_rounds",
                f"已超过最大工具调用轮次 {settings.max_tool_rounds}，任务已终止。",
            )
            events.append(event)
            _persist(state, event)
            return {"tool_round": tool_round, "status": "max_rounds", "events": events}

        last: BaseMessage = state["messages"][-1]
        tool_calls = getattr(last, "tool_calls", None) or []
        import json

        for call in tool_calls:
            name = call.get("name") if isinstance(call, dict) else getattr(call, "name", "")
            args = call.get("args") if isinstance(call, dict) else getattr(call, "args", {})
            event = make_event(
                "tool_call",
                f"调用工具 {name}",
                tool=name,
                input=json.dumps(args, ensure_ascii=False, default=str),
            )
            events.append(event)
            _persist(state, event)

        def _invoke():
            return inner.invoke(state)

        try:
            result = _invoke()
        except Exception as first:
            try:
                result = _invoke()
            except Exception as second:
                event = make_event("error", f"工具连续失败两次，已停止：{second}")
                events.append(event)
                _persist(state, event)
                return {
                    "tool_round": tool_round,
                    "status": "failed",
                    "events": events,
                    "last_error": str(second or first),
                }

        new_messages = result.get("messages") if isinstance(result, dict) else result
        if new_messages:
            for msg in new_messages if isinstance(new_messages, list) else [new_messages]:
                if isinstance(msg, ToolMessage):
                    event = make_event(
                        "tool_result",
                        "工具返回",
                        tool=getattr(msg, "name", None),
                        output=str(msg.content)[:4000],
                    )
                    events.append(event)
                    _persist(state, event)
        return {
            "messages": new_messages,
            "tool_round": tool_round,
            "status": "running",
            "events": events,
        }

    return tools_node


def finalize_node(state: dict) -> dict:
    if is_cancelled(state.get("session_id") or ""):
        result = _cancelled(state)
        _persist(state, result["events"][-1])
        return result
    last = state.get("messages", [None])[-1]
    content = ""
    if isinstance(last, AIMessage):
        content = last.content if isinstance(last.content, str) else str(last.content)
    elif last is not None:
        content = getattr(last, "content", "") or str(last)
    event = make_event("final", content or "（无最终文本）")
    events = _append(state.get("events"), event)
    _persist(state, event)
    return {"status": "completed", "events": events}
