"""运行状态与日志接口（只读）。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from server.auth.routes import require_session
from server.auth.sessions import Session, SessionStore
from server.status.reader import LogResponse, StatusReader, StatusResponse


def build_status_router(reader: StatusReader, sessions: SessionStore) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["status"])
    authed = Annotated[Session, Depends(require_session(sessions))]

    @router.get("/status", response_model=StatusResponse)
    def get_status(session: authed) -> StatusResponse:
        return reader.status()

    @router.get("/logs/{date}", response_model=LogResponse)
    def get_log(date: str, session: authed) -> LogResponse:
        log = reader.log(date)
        if log is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "该日期没有日志")
        return log

    return router
