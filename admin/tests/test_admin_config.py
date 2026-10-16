from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi.testclient import TestClient

from server.settings import AdminSettings


def test_reads_and_normalizes_legacy_messages(authed: TestClient) -> None:
    config = authed.get("/api/config").json()
    assert [f["name"] for f in config["friends"]] == ["好友A", "好友B"]
    assert config["friends"][0]["enabled"] is True
    assert config["friends"][1]["messages"] == [{"type": "douyin_sticker", "sticker": "嗨"}]
    assert config["version"]


def test_save_preserves_other_fields_and_permissions(authed: TestClient, settings: AdminSettings) -> None:
    config = authed.get("/api/config").json()
    config["friends"][0]["enabled"] = False
    config["friends"].append({"name": "好友C", "messages": [{"type": "text", "content": "晚安"}]})

    response = authed.put("/api/config", json=config)

    assert response.status_code == 200, response.text
    assert response.json()["applies_next_run"] is False
    saved = json.loads(settings.task_config.read_text(encoding="utf-8"))
    assert saved["task_id"] == "daily-streak"
    assert saved["send_interval_seconds"] == {"min": 3, "max": 8}
    assert saved["targets"][0]["enabled"] is False
    assert [t["name"] for t in saved["targets"]] == ["好友A", "好友B", "好友C"]
    assert os.stat(settings.task_config).st_mode & 0o777 == 0o600


def test_stale_version_is_rejected(authed: TestClient) -> None:
    config = authed.get("/api/config").json()
    assert authed.put("/api/config", json=config).status_code == 200
    # 用旧的 version 再保存一次，模拟另一个窗口
    assert authed.put("/api/config", json=config).status_code == 409


def test_unknown_sticker_rejected_by_runner_rules(authed: TestClient, settings: AdminSettings) -> None:
    before = settings.task_config.read_bytes()
    config = authed.get("/api/config").json()
    config["friends"][0]["messages"] = [{"type": "douyin_sticker", "sticker": "不存在"}]

    response = authed.put("/api/config", json=config)

    assert response.status_code == 422
    assert "不存在" in response.json()["detail"]
    assert settings.task_config.read_bytes() == before
    leftovers = [p for p in settings.task_config.parent.iterdir() if p.suffix == ".tmp"]
    assert leftovers == []


def test_all_disabled_rejected(authed: TestClient) -> None:
    config = authed.get("/api/config").json()
    for friend in config["friends"]:
        friend["enabled"] = False
    assert authed.put("/api/config", json=config).status_code == 422


def test_duplicate_names_rejected(authed: TestClient) -> None:
    config = authed.get("/api/config").json()
    config["friends"][1]["name"] = "好友A"
    assert authed.put("/api/config", json=config).status_code == 422


def test_unknown_fields_rejected(authed: TestClient) -> None:
    config = authed.get("/api/config").json()
    config["friends"][0]["cookie"] = "x"
    assert authed.put("/api/config", json=config).status_code == 422


def test_save_while_running_reports_next_run(authed: TestClient, settings: AdminSettings) -> None:
    (settings.artifacts_dir / "run.lock").write_text(str(os.getpid()))
    config = authed.get("/api/config").json()

    response = authed.put("/api/config", json=config)

    assert response.status_code == 200
    assert response.json()["applies_next_run"] is True


def test_saved_config_loads_in_runner(authed: TestClient, settings: AdminSettings) -> None:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from app.config import load_task
    from app.models import Settings

    config = authed.get("/api/config").json()
    config["friends"][0]["enabled"] = False
    authed.put("/api/config", json=config)

    task = load_task(Settings(settings.task_config, None, None, True, None, settings.artifacts_dir, False))
    assert [t.name for t in task.targets] == ["好友B"]
