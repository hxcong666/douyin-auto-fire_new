"""登录、退出、当前用户接口，以及其他路由使用的鉴权依赖。

- 会话令牌放在 HttpOnly + SameSite=Strict 的 Cookie 中，前端 JS 读不到。
- 所有修改类请求还要求携带 X-CSRF-Token 请求头，值由 /api/auth/me 返回。
"""

import hmac
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from server.auth.passwords import verify_password
from server.auth.sessions import CSRF_HEADER, SESSION_COOKIE, LoginLimiter, Session, SessionStore
from server.settings import AdminSettings


LOGGER = logging.getLogger("admin.auth")


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class MeResponse(BaseModel):
    username: str
    csrf_token: str


def build_auth_router(settings: AdminSettings, sessions: SessionStore, limiter: LoginLimiter) -> APIRouter:
    router = APIRouter(prefix="/api/auth", tags=["auth"])

    @router.post("/login", response_model=MeResponse)
    def login(body: LoginRequest, request: Request, response: Response) -> MeResponse:
        ip = request.client.host if request.client else "unknown"
        wait = limiter.retry_after(ip)
        if wait:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, f"登录失败次数过多，请 {wait} 秒后再试")
        user_ok = hmac.compare_digest(body.username, settings.username)
        # 用户名错误时也计算一次哈希，避免通过响应时间猜测用户名
        password_ok = verify_password(body.password, settings.password_hash)
        if not (user_ok and password_ok):
            limiter.record_failure(ip)
            LOGGER.warning("登录失败，来源 %s", ip)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "账号或密码错误")
        limiter.record_success(ip)
        LOGGER.info("登录成功，来源 %s", ip)
        token, session = sessions.create(settings.username)
        response.set_cookie(
            SESSION_COOKIE,
            token,
            max_age=settings.session_hours * 3600,
            httponly=True,
            secure=settings.cookie_secure,
            samesite="strict",
            path="/",
        )
        return MeResponse(username=session.username, csrf_token=session.csrf_token)

    @router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
    def logout(request: Request, response: Response) -> None:
        sessions.revoke(request.cookies.get(SESSION_COOKIE))
        response.delete_cookie(SESSION_COOKIE, path="/")

    @router.get("/me", response_model=MeResponse)
    def me(session: Annotated[Session, Depends(require_session(sessions))]) -> MeResponse:
        return MeResponse(username=session.username, csrf_token=session.csrf_token)

    return router


def require_session(sessions: SessionStore):
    def dependency(request: Request) -> Session:
        session = sessions.get(request.cookies.get(SESSION_COOKIE))
        if session is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "未登录或登录已过期")
        return session

    return dependency


def require_csrf(sessions: SessionStore):
    session_dependency = require_session(sessions)

    def dependency(request: Request) -> Session:
        session = session_dependency(request)
        sent = request.headers.get(CSRF_HEADER, "")
        if not hmac.compare_digest(sent, session.csrf_token):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "请求校验失败，请刷新页面")
        return session

    return dependency
