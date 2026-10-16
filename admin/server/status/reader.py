"""运行状态与日志的只读接口模型和读取逻辑。

只读取 artifacts/ 下续火花程序已经脱敏的文件（好友用「好友01」等别名），
不会接触 .env、Cookie、storage-state.json 等登录凭证。
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError

_DAILY_LOG = re.compile(r"^daily_(\d{8})\.log$")
_MAX_LOG_BYTES = 256 * 1024
# 兜底打码：日志正常不含这些，但万一出现也不能下发给浏览器
_URL = re.compile(r"https?://\S+")
_SECRET_PAIR = re.compile(r"(?i)(token|secret|sign|cookie|sessionid|password)(\w*\s*[=:]\s*)\S+")


class TargetResult(BaseModel):
    target: str
    status: Literal["success", "failed", "skipped", "duplicate", "unknown"]
    sent: int = 0
    error: str | None = None


class RunResult(BaseModel):
    task_id: str
    dry_run: bool
    finished_at: str
    results: list[TargetResult]


class History(BaseModel):
    total_runs: int = 0
    total_successful_runs: int = 0
    total_messages_sent: int = 0
    average_success_rate: float = 0.0
    last_run_at: str = ""
    first_run_at: str = ""


class StatusResponse(BaseModel):
    running: bool
    last_run: RunResult | None
    history: History | None
    log_dates: list[str]


class LogResponse(BaseModel):
    date: str
    content: str
    truncated: bool


class StatusReader:
    def __init__(self, artifacts_dir: Path) -> None:
        self.dir = artifacts_dir

    def is_running(self) -> bool:
        """续火花程序运行时会创建 artifacts/run.lock，内容是进程号。"""
        lock = self.dir / "run.lock"
        try:
            pid = int(lock.read_text().strip())
        except (FileNotFoundError, ValueError):
            return lock.exists()
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False  # 进程已退出，锁是残留的
        except PermissionError:
            return True  # 进程存在但属于其他用户
        return True

    def status(self) -> StatusResponse:
        return StatusResponse(
            running=self.is_running(),
            last_run=_load(self.dir / "result.json", RunResult),
            history=_load(self.dir / "metrics_history.json", History),
            log_dates=self.log_dates(),
        )

    def log_dates(self) -> list[str]:
        if not self.dir.is_dir():
            return []
        dates = [m.group(1) for p in self.dir.iterdir() if (m := _DAILY_LOG.match(p.name))]
        return sorted(dates, reverse=True)

    def log(self, date: str) -> LogResponse | None:
        if not re.fullmatch(r"\d{8}", date):
            return None
        path = self.dir / f"daily_{date}.log"
        try:
            size = path.stat().st_size
            with path.open("rb") as handle:
                handle.seek(max(0, size - _MAX_LOG_BYTES))
                data = handle.read()
        except OSError:
            return None
        text = redact_log(data.decode("utf-8", "replace"))
        return LogResponse(date=date, content=text, truncated=size > _MAX_LOG_BYTES)


def redact_log(text: str) -> str:
    text = _URL.sub("<链接已隐藏>", text)
    return _SECRET_PAIR.sub(lambda m: f"{m.group(1)}{m.group(2)}***", text)


def _load(path: Path, model: type[BaseModel]):
    try:
        return model.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValidationError):
        return None
