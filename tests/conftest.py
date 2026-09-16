"""pytest 公共夹具：隔离测试库、重置 schema、提供已登录 client 与 auth 辅助。"""

import os
import tempfile
from pathlib import Path

# 每个 pytest 进程使用独立临时 SQLite，避免污染开发库
_TEST_DB = Path(tempfile.gettempdir()) / f"enterprise_ops_pytest_{os.getpid()}.db"
os.environ["MOCK_DB_PATH"] = str(_TEST_DB)
os.environ["USE_MOCK_DB"] = "true"
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-not-for-prod-32b")
os.environ.setdefault("LLM_PROVIDER", "deepseek")
os.environ.setdefault("DEEPSEEK_API_KEY", "test-deepseek-key")
os.environ.setdefault("KB_ENABLED", "false")
os.environ.setdefault("TASK_TIMEOUT_S", "8")
os.environ.setdefault("MAX_TOOL_ROUNDS", "8")

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db.mysql import init_schema_and_seed, reset_sqlite_for_tests


@pytest.fixture(autouse=True)
def _fresh_db():
    """每个用例前后清空并重建 mock 数据库。"""
    get_settings.cache_clear()
    reset_sqlite_for_tests()
    init_schema_and_seed()
    yield
    reset_sqlite_for_tests()
    get_settings.cache_clear()


@pytest.fixture
def client(_fresh_db):
    """FastAPI TestClient，挂载完整 app。"""
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, username: str, password: str) -> str:
    """登录并返回 access_token。"""
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_header(token: str) -> dict:
    """构造 Bearer Authorization 请求头。"""
    return {"Authorization": f"Bearer {token}"}
