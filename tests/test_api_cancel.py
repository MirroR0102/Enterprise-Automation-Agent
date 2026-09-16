"""会话取消 API：运行中可取消；已完成或已有 final 时忽略。"""

import asyncio

from app.agent.nodes import make_event
from app.runtime import get_session
from tests.conftest import auth_header, login


class SlowGraph:
    async def ainvoke(self, *args, **kwargs):
        await asyncio.sleep(30)
        return {"status": "completed", "events": [], "messages": []}


class InstantCompleteGraph:
    async def ainvoke(self, *args, **kwargs):
        await asyncio.sleep(0.05)
        return {
            "status": "completed",
            "events": [make_event("final", "# 周报\n同比 25%")],
            "messages": [],
        }


def test_cancel_running_task(client, monkeypatch):
    """运行中任务 cancel 后状态变为 cancelled 并写入 cancelled 事件。"""
    monkeypatch.setattr("app.api.chat.get_compiled_graph", lambda: SlowGraph())
    token = login(client, "ops", "ops123")
    headers = auth_header(token)
    session_id = client.post("/api/sessions", headers=headers).json()["session_id"]
    started = client.post(
        f"/api/sessions/{session_id}/messages",
        headers=headers,
        json={"content": "long running"},
    )
    assert started.status_code == 200
    cancelled = client.post(f"/api/sessions/{session_id}/cancel", headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    events = client.get(f"/api/sessions/{session_id}/events", headers=headers)
    assert events.status_code == 200
    body = events.json()
    assert body["status"] == "cancelled"
    types = {item["type"] for item in body["events"]}
    assert "cancelled" in types


def test_cancel_after_completed_keeps_completed(client, monkeypatch):
    """任务已完成后再次 cancel 应返回 ok=false 且保持 completed。"""
    monkeypatch.setattr("app.api.chat.get_compiled_graph", lambda: InstantCompleteGraph())
    token = login(client, "ops", "ops123")
    headers = auth_header(token)
    session_id = client.post("/api/sessions", headers=headers).json()["session_id"]
    started = client.post(
        f"/api/sessions/{session_id}/messages",
        headers=headers,
        json={"content": "done soon"},
    )
    assert started.status_code == 200

    for _ in range(50):
        body = client.get(f"/api/sessions/{session_id}/events", headers=headers).json()
        if body["status"] == "completed":
            break
        import time

        time.sleep(0.05)
    assert body["status"] == "completed"

    again = client.post(f"/api/sessions/{session_id}/cancel", headers=headers)
    assert again.status_code == 200
    payload = again.json()
    assert payload["ok"] is False
    assert payload["status"] == "completed"
    events = client.get(f"/api/sessions/{session_id}/events", headers=headers).json()
    assert events["status"] == "completed"


def test_cancel_ignored_when_final_already_present(client):
    """内存中已有 final 事件时 cancel 应视为已完成并忽略。"""
    token = login(client, "ops", "ops123")
    headers = auth_header(token)
    session_id = client.post("/api/sessions", headers=headers).json()["session_id"]
    rec = get_session(session_id)
    assert rec is not None
    rec.status = "running"
    rec.events.append(make_event("final", "# already done"))

    resp = client.post(f"/api/sessions/{session_id}/cancel", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is False
    assert body["status"] == "completed"
    assert get_session(session_id).status == "completed"
