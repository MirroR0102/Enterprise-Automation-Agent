def test_wrong_password_401(client):
    response = client.post("/api/auth/login", json={"username": "ops", "password": "nope"})
    assert response.status_code == 401


def test_login_returns_token(client):
    response = client.post("/api/auth/login", json={"username": "ops", "password": "ops123"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["role"] == "ops"
    assert body["access_token"]


def test_me_without_token_401(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_ops_cannot_read_logs(client):
    token = client.post("/api/auth/login", json={"username": "ops", "password": "ops123"}).json()[
        "access_token"
    ]
    response = client.get("/api/logs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_dev_can_read_logs(client):
    token = client.post("/api/auth/login", json={"username": "dev", "password": "dev123"}).json()[
        "access_token"
    ]
    response = client.get("/api/logs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "items" in response.json()
