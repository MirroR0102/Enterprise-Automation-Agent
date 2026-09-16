"""认证与 RBAC：登录、/me、开发日志仅 dev 可读。"""


def test_wrong_password_401(client):
    """错误密码应返回 401。"""
    response = client.post("/api/auth/login", json={"username": "ops", "password": "nope"})
    assert response.status_code == 401


def test_login_returns_token(client):
    """正确登录应返回 bearer token 与角色、用户名。"""
    response = client.post("/api/auth/login", json={"username": "ops", "password": "ops123"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["role"] == "ops"
    assert body["username"] == "ops"
    assert body["access_token"]


def test_me_without_token_401(client):
    """未带 token 访问 /api/auth/me 应 401。"""
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_ops_cannot_read_logs(client):
    """ops 角色访问 /api/logs 应 403。"""
    token = client.post("/api/auth/login", json={"username": "ops", "password": "ops123"}).json()[
        "access_token"
    ]
    response = client.get("/api/logs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_dev_can_read_logs(client):
    """dev 角色可读取开发日志列表。"""
    token = client.post("/api/auth/login", json={"username": "dev", "password": "dev123"}).json()[
        "access_token"
    ]
    response = client.get("/api/logs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "items" in response.json()
