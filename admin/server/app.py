"""组装 FastAPI 应用：API 路由、安全响应头、前端静态文件。"""
from __future__ import annotations

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server.auth.routes import build_auth_router
from server.auth.sessions import LoginLimiter, SessionStore
from server.configs.routes import build_config_router
from server.configs.store import ConfigStore
from server.settings import AdminSettings
from server.status.reader import StatusReader
from server.status.routes import build_status_router

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    ),
}


def create_app(settings: AdminSettings) -> FastAPI:
    # 关闭自动生成的接口文档，减少对外暴露的信息
    app = FastAPI(title="续火花管理后台", docs_url=None, redoc_url=None, openapi_url=None)
    sessions = SessionStore(ttl_seconds=settings.session_hours * 3600)
    reader = StatusReader(settings.artifacts_dir)

    app.include_router(build_auth_router(settings, sessions, LoginLimiter()))
    app.include_router(build_config_router(ConfigStore(settings.task_config), reader, sessions))
    app.include_router(build_status_router(reader, sessions))

    @app.middleware("http")
    async def security_headers(request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.update(_SECURITY_HEADERS)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    _mount_frontend(app, settings)
    return app


def _mount_frontend(app: FastAPI, settings: AdminSettings) -> None:
    static_dir = settings.static_dir
    if not (static_dir / "index.html").is_file():
        @app.get("/", include_in_schema=False)
        def missing_frontend() -> Response:
            return Response("前端尚未构建，请先运行 scripts/admin/build-web.sh", media_type="text/plain; charset=utf-8")

        return

    app.mount("/_next", StaticFiles(directory=static_dir / "_next"), name="next-assets")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str) -> Response:
        if path.startswith("api/"):
            return Response(status_code=404)
        # Next.js 静态导出：/login 对应 login.html；未知路径回退到首页
        for candidate in (static_dir / path, static_dir / f"{path}.html"):
            resolved = candidate.resolve()
            if resolved.is_file() and resolved.is_relative_to(static_dir.resolve()):
                return FileResponse(resolved)
        return FileResponse(static_dir / "index.html")
