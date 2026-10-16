"""登录会话与暴力破解防护，全部保存在内存中。

后台只有一个管理员账号、单进程运行，重启后需要重新登录，这是可以接受的代价，
换来的是不必把会话令牌落盘。
"""
from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass, field

SESSION_COOKIE = "admin_session"
CSRF_HEADER = "X-CSRF-Token"


@dataclass(frozen=True)
class Session:
    username: str
    csrf_token: str
    expires_at: float


@dataclass
class _Attempts:
    failures: list[float] = field(default_factory=list)
    locked_until: float = 0.0


class SessionStore:
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def create(self, username: str) -> tuple[str, Session]:
        token = secrets.token_urlsafe(32)
        session = Session(username, secrets.token_urlsafe(32), time.time() + self._ttl)
        with self._lock:
            self._purge()
            self._sessions[token] = session
        return token, session

    def get(self, token: str | None) -> Session | None:
        if not token:
            return None
        with self._lock:
            session = self._sessions.get(token)
            if session and session.expires_at < time.time():
                del self._sessions[token]
                return None
            return session

    def revoke(self, token: str | None) -> None:
        with self._lock:
            self._sessions.pop(token or "", None)

    def _purge(self) -> None:
        now = time.time()
        for key in [k for k, s in self._sessions.items() if s.expires_at < now]:
            del self._sessions[key]


class LoginLimiter:
    """同一来源 IP 在 window 秒内失败 max_failures 次后锁定 lock_seconds 秒。"""

    def __init__(self, max_failures: int = 5, window: int = 300, lock_seconds: int = 900) -> None:
        self._max, self._window, self._lock_seconds = max_failures, window, lock_seconds
        self._by_ip: dict[str, _Attempts] = {}
        self._lock = threading.Lock()

    def retry_after(self, ip: str) -> int:
        with self._lock:
            remaining = self._by_ip.get(ip, _Attempts()).locked_until - time.time()
            return max(0, int(remaining))

    def record_failure(self, ip: str) -> None:
        now = time.time()
        with self._lock:
            attempts = self._by_ip.setdefault(ip, _Attempts())
            attempts.failures = [t for t in attempts.failures if now - t < self._window] + [now]
            if len(attempts.failures) >= self._max:
                attempts.locked_until = now + self._lock_seconds
                attempts.failures.clear()

    def record_success(self, ip: str) -> None:
        with self._lock:
            self._by_ip.pop(ip, None)
