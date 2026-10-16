"""config.json 的读写，负责与定时任务之间的并发安全。

- 写入：先写同目录临时文件，fsync 后 os.replace 原子替换。续火花程序在任何
  时刻读到的都是完整的旧文件或完整的新文件，不会读到写了一半的内容。
- 任务运行中：续火花程序只在启动时读一次配置，运行期间修改不影响本次执行，
  下次运行才生效。为了让用户知情，运行中仍允许保存，但接口会返回提示。
- 多个浏览器窗口同时编辑：保存时校验 version（文件内容指纹），不一致则拒绝，
  避免后保存的覆盖先保存的。
- 后台进程内部用 fcntl 文件锁串行化写入。
- 写入前用续火花程序自身的解析逻辑校验临时文件，校验不通过不会替换原文件。
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from server.configs.runner_rules import normalize_target, validate_with_runner
from server.configs.schema import Friend, FriendsConfig, Sticker

# 后台负责维护的字段；其余字段写回时原样保留
_MANAGED_KEYS = ("targets", "stickers", "friends", "messages")


class ConfigConflictError(RuntimeError):
    """文件在读取之后被其他人修改过。"""


class ConfigFormatError(RuntimeError):
    """现有 config.json 无法解析。"""


class ConfigStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock_path = path.with_name(f".{path.name}.admin.lock")

    def read(self) -> FriendsConfig:
        content = self._read_bytes()
        raw = self._parse(content)
        return FriendsConfig(
            friends=[Friend.model_validate(normalize_target(item)) for item in _targets_of(raw)],
            stickers={k: Sticker.model_validate(v) for k, v in raw.get("stickers", {}).items()},
            version=_fingerprint(content),
        )

    def save(self, config: FriendsConfig) -> FriendsConfig:
        with self._write_lock():
            content = self._read_bytes()
            if _fingerprint(content) != config.version:
                raise ConfigConflictError("配置已被其他人修改，请刷新页面后重新编辑")
            raw = self._parse(content) if content else {}
            merged = {k: v for k, v in raw.items() if k not in _MANAGED_KEYS}
            merged["targets"] = [f.model_dump(exclude_none=True) for f in config.friends]
            merged["stickers"] = {k: s.model_dump(exclude_none=True) for k, s in config.stickers.items()}
            self._atomic_write(json.dumps(merged, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
        return self.read()

    def _read_bytes(self) -> bytes:
        try:
            return self.path.read_bytes()
        except FileNotFoundError:
            return b""

    @staticmethod
    def _parse(content: bytes) -> dict[str, Any]:
        if not content:
            return {}
        try:
            raw = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ConfigFormatError(f"config.json 不是有效 JSON: {exc}") from exc
        if not isinstance(raw, dict):
            raise ConfigFormatError("config.json 顶层必须是对象")
        return raw

    @contextmanager
    def _write_lock(self) -> Iterator[None]:
        with open(self._lock_path, "a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def _atomic_write(self, data: bytes) -> None:
        mode = self.path.stat().st_mode & 0o777 if self.path.exists() else 0o600
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=f".{self.path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(tmp, mode)
            validate_with_runner(Path(tmp))
            os.replace(tmp, self.path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise


def _targets_of(raw: dict[str, Any]) -> list[Any]:
    """兼容旧格式 friends + messages：每个好友共用同一组消息。"""
    if "targets" in raw:
        return list(raw["targets"])
    friends, messages = raw.get("friends", []), raw.get("messages", [])
    return [{"name": name, "messages": messages} for name in friends]


def _fingerprint(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:16]
