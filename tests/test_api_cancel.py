import asyncio

from tests.conftest import auth_header, login


class SlowGraph:
    async def ainvoke(self, *args, **kwargs):
        await asyncio.sleep(30)
        return {"status": "completed", "events": [], "messages": []}


def test_cancel_running_task(client, monkeypatch):
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
