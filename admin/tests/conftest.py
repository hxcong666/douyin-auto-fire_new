from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ADMIN_DIR = Path(__file__).resolve().parents[1]
if str(ADMIN_DIR) not in sys.path:
    sys.path.insert(0, str(ADMIN_DIR))

from server.app import create_app  # noqa: E402
from server.auth.passwords import hash_password  # noqa: E402
from server.settings import AdminSettings  # noqa: E402

PASSWORD = "correct-horse-battery"

BASE_CONFIG = {
    "task_id": "daily-streak",
    "timezone": "Asia/Shanghai",
    "targets": [
        {"name": "好友A", "messages": [{"type": "text", "content": "早上好"}]},
        {"name": "好友B", "messages": [{"type": "sticker", "value": "嗨"}]},
    ],
    "stickers": {"嗨": {"label": "嗨"}},
    "send_interval_seconds": {"min": 3, "max": 8},
    "continue_on_error": True,
}


@pytest.fixture
def workdir(tmp_path: Path) -> Path:
    (tmp_path / "artifacts").mkdir()
    config = tmp_path / "config.json"
    config.write_text(json.dumps(BASE_CONFIG, ensure_ascii=False), encoding="utf-8")
    config.chmod(0o600)
    return tmp_path


@pytest.fixture
def settings(workdir: Path) -> AdminSettings:
    return AdminSettings(
        username="admin",
        password_hash=hash_password(PASSWORD),
        host="127.0.0.1",
        port=0,
        cookie_secure=False,
        session_hours=1,
        task_config=workdir / "config.json",
        artifacts_dir=workdir / "artifacts",
        static_dir=workdir / "no-frontend",
        logs_dir=workdir / "logs",
    )


@pytest.fixture
def client(settings: AdminSettings) -> TestClient:
    return TestClient(create_app(settings))


@pytest.fixture
def authed(client: TestClient) -> TestClient:
    response = client.post("/api/auth/login", json={"username": "admin", "password": PASSWORD})
    assert response.status_code == 200
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    return client
