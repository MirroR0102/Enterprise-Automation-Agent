"""周报 API：保存、列表、详情及用户隔离。"""

from app.db import user_store
from tests.conftest import auth_header, login


def test_save_and_list_weekly_reports(client):
    """保存周报后可通过列表与详情 API 读回 Markdown。"""
    token = login(client, "ops", "ops123")
    headers = auth_header(token)
    # ensure user via me
    me = client.get("/api/auth/me", headers=headers).json()
    uid = me["id"]
    user_store.save_weekly_report(uid, "sess-demo", "# 测试周报\n内容", title="测试周报")
    listed = client.get("/api/reports", headers=headers)
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert items
    assert items[0]["title"] == "测试周报"
    rid = items[0]["id"]
    detail = client.get(f"/api/reports/{rid}", headers=headers)
    assert detail.status_code == 200
    assert "测试周报" in detail.json()["markdown"]


def test_reports_isolated_per_user(client):
    """ops 用户的周报不应出现在 dev 用户的列表中。"""
    ops = auth_header(login(client, "ops", "ops123"))
    dev = auth_header(login(client, "dev", "dev123"))
    ops_id = client.get("/api/auth/me", headers=ops).json()["id"]
    user_store.save_weekly_report(ops_id, "s1", "# only ops", title="ops-only")
    ops_list = client.get("/api/reports", headers=ops).json()["items"]
    dev_list = client.get("/api/reports", headers=dev).json()["items"]
    assert any(i["title"] == "ops-only" for i in ops_list)
    assert not any(i["title"] == "ops-only" for i in dev_list)
