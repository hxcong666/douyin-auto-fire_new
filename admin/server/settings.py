"""后台运行配置，从项目根目录的 .env.admin 读取。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class SettingsError(RuntimeError):
    pass


@dataclass(frozen=True)
class AdminSettings:
    username: str
    password_hash: str
    host: str
    port: int
    cookie_secure: bool
    session_hours: int
    task_config: Path
    artifacts_dir: Path
    static_dir: Path
    logs_dir: Path


def load_admin_settings(env_file: Path | None = None) -> AdminSettings:
    path = env_file or Path(os.getenv("ADMIN_ENV_FILE", PROJECT_ROOT / ".env.admin"))
    values = {k: v for k, v in dotenv_values(path).items() if v is not None}

    def get(key: str, default: str = "") -> str:
        return os.getenv(key, values.get(key, default)).strip()

    username = get("ADMIN_USERNAME")
    password_hash = get("ADMIN_PASSWORD_HASH")
    if not username or not password_hash:
        raise SettingsError(f"未配置后台账号，请先运行 scripts/admin/set-password.sh（配置文件: {path}）")

    return AdminSettings(
        username=username,
        password_hash=password_hash,
        host=get("ADMIN_HOST", "127.0.0.1"),
        port=int(get("ADMIN_PORT", "8090")),
        cookie_secure=get("ADMIN_COOKIE_SECURE", "false").lower() == "true",
        session_hours=int(get("ADMIN_SESSION_HOURS", "12")),
        task_config=_resolve(get("ADMIN_TASK_CONFIG", "config.json")),
        artifacts_dir=_resolve(get("ADMIN_ARTIFACTS_DIR", "artifacts")),
        static_dir=_resolve(get("ADMIN_STATIC_DIR", "admin/web/out")),
        logs_dir=_resolve(get("ADMIN_LOGS_DIR", "logs")),
    )


def _resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path
