import datetime

import jwt
import pytest

from app.auth import check_auth_config, hash_password

PROTECTED = [
    "/weights", "/weight-goals", "/money/summary", "/calendar/agenda/today",
    "/invest/portfolio", "/career/pipeline", "/dashboard", "/auth/me",
]
PUBLIC = ["/", "/healthz", "/readyz", "/docs", "/openapi.json", "/auth/config"]


def login(client, username="luke", password="correct horse"):
    return client.post("/auth/login", json={"username": username, "password": password})


def test_auth_disabled_by_default(client):
    assert client.get("/auth/config").json() == {"auth_enabled": False}
    for path in PROTECTED:
        assert client.get(path).status_code == 200, path

    response = login(client)
    assert response.status_code == 400


def test_auth_enabled_blocks_without_token(client, auth_on):
    assert client.get("/auth/config").json() == {"auth_enabled": True}

    for path in PROTECTED:
        response = client.get(path)
        assert response.status_code == 401, path
        assert response.headers["www-authenticate"] == "Bearer"

    for path in PUBLIC:
        assert client.get(path).status_code == 200, path


def test_login_and_use_token(client, auth_on):
    assert login(client, password="wrong").status_code == 401
    assert login(client, username="someone").status_code == 401

    response = login(client)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 3600

    headers = {"Authorization": f"Bearer {body['access_token']}"}
    for path in PROTECTED:
        assert client.get(path, headers=headers).status_code == 200, path

    assert client.get("/auth/me", headers=headers).json()["username"] == "luke"

    # Writes are protected too
    response = client.post("/weights", json={"weight": 200, "measurement_date": "2026-10-01"})
    assert response.status_code == 401
    response = client.post(
        "/weights", json={"weight": 200, "measurement_date": "2026-10-01"}, headers=headers
    )
    assert response.status_code == 200


def test_login_with_bcrypt_hash(client, auth_on, monkeypatch):
    monkeypatch.setattr(auth_on, "app_password", "")
    monkeypatch.setattr(auth_on, "app_password_hash", hash_password("s3cret-pass"))

    assert login(client, password="correct horse").status_code == 401
    assert login(client, password="s3cret-pass").status_code == 200
    # bcrypt only accepts 72 bytes; longer input must fail cleanly, not 500
    assert login(client, password="x" * 100).status_code == 401


def test_bad_tokens_rejected(client, auth_on):
    def token(**overrides):
        now = datetime.datetime.now(datetime.UTC)
        payload = {"sub": "luke", "iat": now, "exp": now + datetime.timedelta(minutes=5)}
        payload.update(overrides)
        secret = overrides.pop("secret", auth_on.jwt_secret)
        payload.pop("secret", None)
        return jwt.encode(payload, secret, algorithm="HS256")

    cases = {
        "expired": token(exp=datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=1)),
        "wrong secret": token(secret="not-the-secret-not-the-secret-123"),
        "wrong user": token(sub="mallory"),
        "garbage": "not.a.jwt",
    }
    for name, value in cases.items():
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {value}"})
        assert response.status_code == 401, name

    assert client.get(
        "/dashboard", headers={"Authorization": f"Bearer {token()}"}
    ).status_code == 200


def test_check_auth_config(auth_on, monkeypatch):
    check_auth_config()  # valid config passes

    monkeypatch.setattr(auth_on, "jwt_secret", "")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        check_auth_config()

    monkeypatch.setattr(auth_on, "jwt_secret", "x" * 32)
    monkeypatch.setattr(auth_on, "app_password", "")
    with pytest.raises(RuntimeError, match="APP_PASSWORD"):
        check_auth_config()

    monkeypatch.setattr(auth_on, "auth_enabled", False)
    check_auth_config()  # anything goes when auth is off
