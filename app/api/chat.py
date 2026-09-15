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
_background: set[asyncio.Task] = set()


class MessageBody(BaseModel):
    content: str = Field(min_length=1)


def _owned(session_id: str, user: User) -> SessionRecord:
    rec = get_session(session_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    if rec.user_id != user.id and user.role != "dev":
        raise HTTPException(status_code=403, detail="无权访问该会话")
    return rec


@router.post("/sessions")
def create_chat_session(user: User = Depends(get_current_user)) -> dict:
    session_id = str(uuid.uuid4())
    create_session(session_id, user.id)
    return {"session_id": session_id}


@router.post("/sessions/{session_id}/messages")
async def post_message(
    session_id: str,
    body: MessageBody,
    user: User = Depends(get_current_user),
) -> dict:
    rec = _owned(session_id, user)
    if rec.task is not None and not rec.task.done():
        raise HTTPException(status_code=409, detail="当前会话已有任务在执行")
    rec.status = "running"
    user_event = make_event("user_input", body.content)
    rec.events.append(user_event)
    log_event(session_id, "user_input", user_event, user_id=user.id)
    clear_cancelled(session_id)
    task = asyncio.create_task(_run_agent(rec, body.content, user.id))
    rec.task = task
    _background.add(task)
    task.add_done_callback(_background.discard)
    return {"ok": True, "status": "running"}


@router.get("/sessions/{session_id}/events")
def get_events(session_id: str, user: User = Depends(get_current_user)) -> dict:
    rec = _owned(session_id, user)
    return {"session_id": session_id, "status": rec.status, "events": rec.events}


@router.get("/sessions/{session_id}/stream")
async def stream_events(session_id: str, user: User = Depends(get_current_user)):
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


@router.post("/sessions/{session_id}/cancel")
async def cancel_session(session_id: str, user: User = Depends(get_current_user)) -> dict:
    rec = _owned(session_id, user)
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
        if is_cancelled(rec.session_id):
            rec.status = "cancelled"
            return
        rec.status = result.get("status") or "completed"
        _merge_events(rec, result.get("events") or [])
        if rec.status == "completed":
            log_event(rec.session_id, "final", {"type": "final", "content": _final_text(result)}, user_id=user_id)
    except asyncio.TimeoutError:
        rec.status = "timeout"
        event = make_event("timeout", f"任务超过 {settings.task_timeout_s} 秒，已强制终止。")
        rec.events.append(event)
        log_event(rec.session_id, "timeout", event, user_id=user_id)
    except asyncio.CancelledError:
        rec.status = "cancelled"
        raise
    except Exception as exc:  # noqa: BLE001
        rec.status = "failed"
        event = make_event("error", str(exc))
        rec.events.append(event)
        log_event(rec.session_id, "error", event, user_id=user_id)


def _merge_events(rec: SessionRecord, events: list[dict[str, Any]]) -> None:
    existing = {(e.get("type"), e.get("timestamp"), e.get("content")) for e in rec.events}
    for event in events:
        key = (event.get("type"), event.get("timestamp"), event.get("content"))
        if key not in existing:
            rec.events.append(event)


def _final_text(result: dict) -> str:
    messages = result.get("messages") or []
    if not messages:
        return ""
    last = messages[-1]
    return getattr(last, "content", "") or ""
