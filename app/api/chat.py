"""对话 API：会话创建、消息提交、SSE 流式事件与取消。"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from app.agent.graph import get_compiled_graph
from app.agent.nodes import make_event
from app.auth.deps import get_current_user
from app.auth.models import User
from app.config import get_settings
from app.db import user_store
from app.logging_service import log_event
from app.runtime import (
    SessionRecord,
    clear_cancelled,
    create_session,
    get_session,
    is_cancelled,
    set_cancelled,
)

router = APIRouter(prefix="/api", tags=["chat"])
# 持有后台 asyncio.Task 强引用，避免 GC 导致任务静默消失
_background: set[asyncio.Task] = set()


class MessageBody(BaseModel):
    """用户消息请求体。"""

    content: str = Field(min_length=1)


def _owned(session_id: str, user: User) -> SessionRecord:
    """校验会话归属；dev 角色可访问任意会话。"""
    rec = get_session(session_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    if rec.user_id != user.id and user.role != "dev":
        raise HTTPException(status_code=403, detail="无权访问该会话")
    return rec


@router.post("/sessions")
def create_chat_session(user: User = Depends(get_current_user)) -> dict:
    """创建新对话会话并初始化用户侧存储。"""
    user_store.ensure_user_store(user.id)
    session_id = str(uuid.uuid4())
    create_session(session_id, user.id)
    user_store.ensure_conversation(user.id, session_id, title="新对话")
    return {"session_id": session_id}


@router.post("/sessions/{session_id}/messages")
async def post_message(
    session_id: str,
    body: MessageBody,
    user: User = Depends(get_current_user),
) -> dict:
    """提交用户消息并异步启动 Agent；同会话互斥，运行中则 409。"""
    rec = _owned(session_id, user)
    # 取消互斥：同一会话只允许一个未完成任务
    if rec.task is not None and not rec.task.done():
        raise HTTPException(status_code=409, detail="当前会话已有任务在执行")
    rec.status = "running"
    user_event = make_event("user_input", body.content)
    rec.events.append(user_event)
    log_event(session_id, "user_input", user_event, user_id=user.id)
    try:
        user_store.add_message(user.id, session_id, "user", body.content)
        user_store.add_tool_event(user.id, session_id, user_event)
    except Exception:
        pass
    clear_cancelled(session_id)
    task = asyncio.create_task(_run_agent(rec, body.content, user.id))
    rec.task = task
    _background.add(task)
    task.add_done_callback(_background.discard)
    return {"ok": True, "status": "running"}


@router.get("/sessions/{session_id}/events")
def get_events(session_id: str, user: User = Depends(get_current_user)) -> dict:
    """轮询获取会话事件列表与当前状态。"""
    rec = _owned(session_id, user)
    return {"session_id": session_id, "status": rec.status, "events": rec.events}


@router.get("/sessions/{session_id}/stream")
async def stream_events(session_id: str, user: User = Depends(get_current_user)):
    """SSE 推送事件；终态时发送 done 并关闭流。"""
    rec = _owned(session_id, user)

    async def generate():
        last = 0
        terminal = {"completed", "failed", "cancelled", "timeout", "max_rounds"}
        while True:
            while last < len(rec.events):
                yield f"data: {json.dumps(rec.events[last], ensure_ascii=False)}\n\n"
                last += 1
            if rec.status in terminal:
                yield f"data: {json.dumps({'type': 'done', 'status': rec.status}, ensure_ascii=False)}\n\n"
                break
            await asyncio.sleep(0.25)

    return StreamingResponse(generate(), media_type="text/event-stream")


# 已结束状态不可再取消
NON_CANCELABLE = frozenset({"completed", "failed", "timeout", "max_rounds"})


def _has_final_event(rec: SessionRecord) -> bool:
    """是否已产出 final 事件（与 completed 判定联动）。"""
    return any(e.get("type") == "final" for e in rec.events)


@router.post("/sessions/{session_id}/cancel")
async def cancel_session(session_id: str, user: User = Depends(get_current_user)) -> dict:
    """人工取消：设置取消标志、更新状态并 cancel 后台任务。"""
    rec = _owned(session_id, user)
    if rec.status in NON_CANCELABLE:
        return {
            "ok": False,
            "status": rec.status,
            "reason": "任务已结束，无法取消",
        }
    # 已有终稿则视为 completed，忽略取消请求
    if _has_final_event(rec):
        rec.status = "completed"
        return {
            "ok": False,
            "status": "completed",
            "reason": "已有最终报告，忽略取消",
        }
    if rec.status not in {"running", "idle"}:
        return {"ok": False, "status": rec.status, "reason": "当前状态不可取消"}

    set_cancelled(session_id, True)
    rec.status = "cancelled"
    event = make_event("cancelled", "任务已被人工终止")
    rec.events.append(event)
    log_event(session_id, "cancelled", event, user_id=user.id)
    task = rec.task
    if task is not None and not task.done():
        task.cancel()
    return {"ok": True, "status": "cancelled"}


async def _run_agent(rec: SessionRecord, content: str, user_id: int) -> None:
    """后台执行 LangGraph；超时/取消/异常时更新会话状态并落库。"""
    settings = get_settings()
    graph = get_compiled_graph()
    config = {"configurable": {"thread_id": rec.session_id}}
    initial = {
        "messages": [HumanMessage(content=content)],
        "session_id": rec.session_id,
        "user_id": user_id,
        "tool_round": 0,
        "status": "running",
        "events": [],
    }
    try:
        result = await asyncio.wait_for(
            graph.ainvoke(initial, config),
            timeout=settings.task_timeout_s,
        )
        _merge_events(rec, result.get("events") or [])
        result_status = result.get("status") or "completed"
        if _has_final_event(rec) or result_status == "completed":
            rec.status = "completed"
            final_text = _final_text(result) or _final_from_events(rec)
            log_event(
                rec.session_id,
                "final",
                {"type": "final", "content": final_text},
                user_id=user_id,
            )
            try:
                if final_text:
                    user_store.add_message(user_id, rec.session_id, "assistant", final_text)
                    user_store.save_weekly_report(
                        user_id,
                        rec.session_id,
                        final_text,
                        file_relpath="reports/",
                    )
            except Exception:
                pass
            return
        if is_cancelled(rec.session_id):
            rec.status = "cancelled"
            return
        rec.status = result_status
    except asyncio.TimeoutError:
        # 超时但已有 final 则仍算 completed
        if _has_final_event(rec):
            rec.status = "completed"
            return
        rec.status = "timeout"
        event = make_event("timeout", f"任务超过 {settings.task_timeout_s} 秒，已强制终止。")
        rec.events.append(event)
        log_event(rec.session_id, "timeout", event, user_id=user_id)
    except asyncio.CancelledError:
        if _has_final_event(rec):
            rec.status = "completed"
            return
        rec.status = "cancelled"
        raise
    except Exception as exc:  # noqa: BLE001
        rec.status = "failed"
        event = make_event("error", str(exc))
        rec.events.append(event)
        log_event(rec.session_id, "error", event, user_id=user_id)


def _merge_events(rec: SessionRecord, events: list[dict[str, Any]]) -> None:
    """按 (type, timestamp, content) 去重合并图内产生的事件。"""
    existing = {(e.get("type"), e.get("timestamp"), e.get("content")) for e in rec.events}
    for event in events:
        key = (event.get("type"), event.get("timestamp"), event.get("content"))
        if key not in existing:
            rec.events.append(event)


def _final_text(result: dict) -> str:
    """从图返回的最后一条消息提取正文。"""
    messages = result.get("messages") or []
    if not messages:
        return ""
    last = messages[-1]
    return getattr(last, "content", "") or ""


def _final_from_events(rec: SessionRecord) -> str:
    """从事件流倒序查找 final 事件内容。"""
    for event in reversed(rec.events):
        if event.get("type") == "final":
            return str(event.get("content") or "")
    return ""
