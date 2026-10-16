from __future__ import annotations

import json

from fastapi.testclient import TestClient

from server.settings import AdminSettings
from server.status.reader import redact_log


def test_status_without_runs(authed: TestClient) -> None:
    body = authed.get("/api/status").json()
    assert body == {"running": False, "last_run": None, "history": None, "log_dates": []}


def test_status_reads_results(authed: TestClient, settings: AdminSettings) -> None:
    result = {
        "task_id": "daily-streak",
        "dry_run": False,
        "finished_at": "2026-10-16T09:09:55+08:00",
        "results": [{"target": "好友01", "status": "failed", "sent": 0, "error": "搜索不到目标好友"}],
    }
    (settings.artifacts_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    (settings.artifacts_dir / "daily_20261016.log").write_text("ok", encoding="utf-8")

    body = authed.get("/api/status").json()

    assert body["last_run"]["results"][0]["error"] == "搜索不到目标好友"
    assert body["log_dates"] == ["20261016"]


def test_stale_lock_is_not_running(authed: TestClient, settings: AdminSettings) -> None:
    (settings.artifacts_dir / "run.lock").write_text("999999999")
    assert authed.get("/api/status").json()["running"] is False


def test_log_is_redacted(authed: TestClient, settings: AdminSettings) -> None:
    (settings.artifacts_dir / "daily_20261016.log").write_text(
        "通知 https://open.feishu.cn/hook/abc token=abc123 正常行", encoding="utf-8"
    )

    content = authed.get("/api/logs/20261016").json()["content"]

    assert "abc123" not in content and "feishu" not in content
    assert "正常行" in content


def test_log_date_must_be_digits(authed: TestClient) -> None:
    assert authed.get("/api/logs/..%2F.env").status_code == 404
    assert authed.get("/api/logs/2026101").status_code == 404


def test_redact_secret_pairs() -> None:
    for line in ("FEISHU_SECRET=xyz", "secret: xyz", "sessionid=xyz", "Cookie: xyz"):
        assert "xyz" not in redact_log(line), line
