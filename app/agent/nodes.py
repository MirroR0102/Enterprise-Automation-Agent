"""LangGraph 节点实现：LLM 推理、工具调用、终稿汇总与事件持久化。

agent 节点优先 astream：无工具调用时推送 final_delta（终稿逐字）；
有工具调用时推送 thought。tools 节点在线程中执行，避免堵死事件循环。
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import ToolNode

from app.agent.prompts import SYSTEM_PROMPT
from app.config import get_settings
from app.runtime import is_cancelled


def utc_now() -> str:
    """返回 UTC ISO 时间戳，供事件记录使用。"""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_event(
    event_type: str,
    content: str,
    *,
    tool: str | None = None,
    input: str | None = None,
    output: str | None = None,
) -> dict[str, Any]:
    """构造标准 SSE/日志事件字典。"""
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
    """用户取消时写入 cancelled 状态与对应事件。"""
    event = make_event("cancelled", "任务已被人工终止")
    return {
        "status": "cancelled",
        "events": _append(state.get("events"), event),
    }


def _persist(state: dict, event: dict) -> None:
    """将事件写入内存会话（SSE 可读）；终态类事件同步落库。delta 不写 DB 以免刷爆日志。"""
    from app.logging_service import log_event
    from app.runtime import get_session

    et = event.get("type")
    if et not in {"final_delta", "stream_reset"}:
        log_event(state.get("session_id") or "", et, event, user_id=state.get("user_id"))
    rec = get_session(state.get("session_id") or "")
    if rec is not None:
        rec.events.append(event)
        if et in {"cancelled", "failed", "timeout", "max_rounds", "final"}:
            mapping = {
                "cancelled": "cancelled",
                "failed": "failed",
                "timeout": "timeout",
                "max_rounds": "max_rounds",
                "final": "completed",
            }
            rec.status = mapping[et]


def get_llm(llm=None):
    """按配置选择 DeepSeek / OpenAI / 通义千问兼容接口；可注入 mock LLM。"""
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


def _chunk_text(chunk: Any) -> str:
    """从流式 chunk 提取文本增量。"""
    content = getattr(chunk, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text") or ""))
        return "".join(parts)
    return ""


def _chunk_has_tool_calls(chunk: Any) -> bool:
    """判断 chunk 是否携带工具调用碎片或完整 tool_calls。"""
    tcc = getattr(chunk, "tool_call_chunks", None) or []
    if tcc:
        return True
    tool_calls = getattr(chunk, "tool_calls", None) or []
    return bool(tool_calls)


async def _invoke_llm(bound: Any, messages: list) -> Any:
    """无 astream 时在线程池里同步 invoke，避免阻塞事件循环。"""
    invoke = getattr(bound, "invoke", None)
    if invoke is None:
        raise RuntimeError("LLM 不可调用")
    return await asyncio.to_thread(invoke, messages)


async def _stream_or_invoke(bound: Any, messages: list, state: dict, events: list) -> tuple[Any, list]:
    """流式调用 LLM：无工具时推 final_delta；有工具时结束推 thought。"""
    astream = getattr(bound, "astream", None)
    if not callable(astream):
        response = await _invoke_llm(bound, messages)
        thought = getattr(response, "content", "") or ""
        tool_calls = getattr(response, "tool_calls", None) or []
        if tool_calls:
            if thought:
                event = make_event("thought", thought if isinstance(thought, str) else str(thought))
                events.append(event)
                _persist(state, event)
        else:
            text = thought if isinstance(thought, str) else str(thought)
            if text:
                # 非流式模型：按小块推送，仍让前端有打字效果且让出事件循环
                step = 24
                for i in range(0, len(text), step):
                    piece = text[i : i + step]
                    event = make_event("final_delta", piece)
                    events.append(event)
                    _persist(state, event)
                    await asyncio.sleep(0)
        return response, events

    accumulated = None
    saw_tools = False
    emitted_delta = False
    full_text = ""

    async for chunk in astream(messages):
        if is_cancelled(state.get("session_id") or ""):
            break
        accumulated = chunk if accumulated is None else accumulated + chunk
        if _chunk_has_tool_calls(chunk):
            if not saw_tools and emitted_delta:
                # 先当终稿流了，随后发现要调工具 → 通知前端清空草稿
                reset = make_event("stream_reset", "模型改为调用工具，清空周报草稿")
                events.append(reset)
                _persist(state, reset)
                emitted_delta = False
            saw_tools = True
        piece = _chunk_text(chunk)
        if piece:
            full_text += piece
            if not saw_tools:
                event = make_event("final_delta", piece)
                events.append(event)
                _persist(state, event)
                emitted_delta = True

    if accumulated is None:
        response = await _invoke_llm(bound, messages)
    else:
        response = accumulated

    tool_calls = getattr(response, "tool_calls", None) or []
    if tool_calls or saw_tools:
        thought = full_text or getattr(response, "content", "") or ""
        if thought:
            event = make_event(
                "thought",
                thought if isinstance(thought, str) else str(thought),
            )
            events.append(event)
            _persist(state, event)
    return response, events


def build_agent_node(llm=None, tools=None):
    """返回异步 agent 节点：流式推送 final_delta / thought。"""

    async def agent_node(state: dict) -> dict:
        if is_cancelled(state.get("session_id") or ""):
            result = _cancelled(state)
            _persist(state, result["events"][-1])
            return result

        bound = get_llm(llm).bind_tools(tools or [])
        messages = [SystemMessage(content=SYSTEM_PROMPT), *state.get("messages", [])]
        events = list(state.get("events") or [])
        response, events = await _stream_or_invoke(bound, messages, state, events)
        return {"messages": [response], "events": events, "status": "running"}

    return agent_node


def build_tools_node(tools):
    """返回异步 tools 节点：记录 tool_call/result，限制轮次，失败时重试一次。"""
    try:
        inner = ToolNode(tools, handle_tool_errors=False)
    except TypeError:
        inner = ToolNode(tools)

    async def tools_node(state: dict) -> dict:
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
            result = await asyncio.to_thread(_invoke)
        except Exception as first:
            try:
                result = await asyncio.to_thread(_invoke)
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


async def finalize_node(state: dict) -> dict:
    """无更多 tool_calls 时提取最终 AI 回复，写入 final 事件并标记 completed。"""
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
