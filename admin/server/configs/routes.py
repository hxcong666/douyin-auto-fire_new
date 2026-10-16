"""好友与消息配置接口。"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from server.auth.routes import require_csrf, require_session
from server.auth.sessions import Session, SessionStore
from server.configs.runner_rules import ConfigInvalidError
from server.configs.schema import FriendsConfig
from server.configs.store import ConfigConflictError, ConfigFormatError, ConfigStore
from server.status.reader import StatusReader


LOGGER = logging.getLogger("admin.config")


class SaveResponse(BaseModel):
    config: FriendsConfig
    # 保存时定时任务正在运行：本次运行仍使用旧配置，下次运行才生效
    applies_next_run: bool


def build_config_router(store: ConfigStore, reader: StatusReader, sessions: SessionStore) -> APIRouter:
    router = APIRouter(prefix="/api/config", tags=["config"])
    authed = Annotated[Session, Depends(require_session(sessions))]
    csrf = Annotated[Session, Depends(require_csrf(sessions))]

    @router.get("", response_model=FriendsConfig)
    def get_config(session: authed) -> FriendsConfig:
        try:
            return store.read()
        except ConfigFormatError as exc:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc)) from exc

    @router.put("", response_model=SaveResponse)
    def save_config(body: FriendsConfig, session: csrf) -> SaveResponse:
        _check_names(body)
        try:
            saved = store.save(body)
        except ConfigConflictError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        except (ConfigInvalidError, ConfigFormatError) as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
        running = reader.is_running()
        # 只记录数量，不记录好友昵称和消息内容
        enabled = sum(f.enabled for f in saved.friends)
        LOGGER.info("%s 保存配置：好友 %d 位（启用 %d），任务运行中=%s", session.username, len(saved.friends), enabled, running)
        return SaveResponse(config=saved, applies_next_run=running)

    return router


def _check_names(body: FriendsConfig) -> None:
    names = [f.name for f in body.friends]
    duplicated = sorted({n for n in names if names.count(n) > 1})
    if duplicated:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"好友名称重复: {', '.join(duplicated)}")
