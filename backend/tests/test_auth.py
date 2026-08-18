from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD


def test_login_success(client):
    res = client.post("/auth/login", data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert res.status_code == 200
    body = res.json()
    assert body["access_token"]
    assert body["user"]["email"] == ADMIN_EMAIL


def test_login_wrong_password(client):
    res = client.post("/auth/login", data={"username": ADMIN_EMAIL, "password": "errada"})
    assert res.status_code == 401


def test_me_requires_token(client):
    res = client.get("/auth/me")
    assert res.status_code == 401


def test_me_with_token(client, admin_headers):
    res = client.get("/auth/me", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["email"] == ADMIN_EMAIL


def test_login_rate_limit_blocks_after_10_failures(client):
    for _ in range(10):
        res = client.post("/auth/login", data={"username": ADMIN_EMAIL, "password": "errada"})
        assert res.status_code == 401

    res = client.post("/auth/login", data={"username": ADMIN_EMAIL, "password": "errada"})
    assert res.status_code == 429
    assert "Retry-After" in res.headers

    # mesmo com a senha certa, continua bloqueado até a janela expirar
    res = client.post("/auth/login", data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert res.status_code == 429


def test_login_success_resets_rate_limit_counter(client):
    for _ in range(5):
        res = client.post("/auth/login", data={"username": ADMIN_EMAIL, "password": "errada"})
        assert res.status_code == 401

    res = client.post("/auth/login", data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert res.status_code == 200

    for _ in range(9):
        res = client.post("/auth/login", data={"username": ADMIN_EMAIL, "password": "errada"})
        assert res.status_code == 401
