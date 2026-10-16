"""用续火花程序自身的解析逻辑校验配置，保证网页保存的内容一定能被定时任务读取。

同时把旧格式消息（{"type": "sticker", "value": ...}）规范化为后台使用的格式。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from server.settings import PROJECT_ROOT

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import ConfigError, load_task  # noqa: E402
from app.models import Settings  # noqa: E402


class ConfigInvalidError(ValueError):
    """配置不能被续火花程序接受。"""


def validate_with_runner(config_path: Path) -> None:
    settings = Settings(
        task_config_path=config_path,
        storage_state=None,
        cookie=None,
        headless=True,
        browser_path=None,
        artifacts_dir=config_path.parent / "artifacts",
        trace=False,
    )
    try:
        load_task(settings)
    except ConfigError as exc:
        raise ConfigInvalidError(str(exc)) from exc


_VALUE_FIELD = {"text": "content", "douyin_sticker": "sticker", "image": "path"}


def normalize_message(raw: Any) -> Any:
    """旧格式 type=sticker 和 value 字段，转换为 douyin_sticker 和具体字段名。"""
    if not isinstance(raw, dict):
        return raw
    item = dict(raw)
    if item.get("type") == "sticker":
        item["type"] = "douyin_sticker"
    if item.get("type") == "random":
        item["choices"] = [normalize_message(c) for c in item.get("choices", [])]
        return item
    field = _VALUE_FIELD.get(str(item.get("type")))
    if field and "value" in item:
        item.setdefault(field, item.pop("value"))
    return item


def normalize_target(raw: Any) -> Any:
    if not isinstance(raw, dict):
        return raw
    item = dict(raw)
    item["messages"] = [normalize_message(m) for m in item.get("messages", [])]
    return item
