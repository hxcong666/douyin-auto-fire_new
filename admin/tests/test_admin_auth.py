from __future__ import annotations

from fastapi.testclient import TestClient

from server.auth.passwords import hash_password, verify_password
from tests.conftest import PASSWORD


def test_password_hash_roundtrip() -> None:
    encoded = hash_password("secret-value-123")
    assert "secret-value-123" not in encoded
    assert verify_password("secret-value-123", encoded)
    assert not verify_password("wrong", encoded)
    assert not verify_password("x", "garbage")


def test_api_requires_login(client: TestClient) -> None:
    assert client.get("/api/config").status_code == 401
    assert client.get("/api/status").status_code == 401
    assert client.get("/api/logs/20260101").status_code == 401


def test_session_cookie_is_httponly_and_strict(client: TestClient) -> None:
    response = client.post("/api/auth/login", json={"username": "admin", "password": PASSWORD})
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=strict" in cookie


def test_wrong_password_rejected(client: TestClient) -> None:
    response = client.post("/api/auth/login", json={"username": "admin", "password": "nope"})
    assert response.status_code == 401


def test_login_locked_after_repeated_failures(client: TestClient) -> None:
    for _ in range(5):
        client.post("/api/auth/login", json={"username": "admin", "password": "nope"})
    response = client.post("/api/auth/login", json={"username": "admin", "password": PASSWORD})
    assert response.status_code == 429


def test_write_requires_csrf_token(authed: TestClient) -> None:
    config = authed.get("/api/config").json()
    del authed.headers["X-CSRF-Token"]
    assert authed.put("/api/config", json=config).status_code == 403


def test_logout_revokes_session(authed: TestClient) -> None:
    assert authed.post("/api/auth/logout").status_code == 204
    assert authed.get("/api/config").status_code == 401


def test_security_headers_present(client: TestClient) -> None:
    response = client.get("/api/status")
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_api_docs_disabled(client: TestClient) -> None:
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert "openapi" not in client.get(path).text.lower()
