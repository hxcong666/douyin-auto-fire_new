"""管理后台启动入口：uv run python main.py"""
from __future__ import annotations

import uvicorn

from server.logging_setup import configure_logging
from server.settings import load_admin_settings
from server.app import create_app


def main() -> None:
    settings = load_admin_settings()
    configure_logging(settings.logs_dir)
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port, log_config=None, proxy_headers=False)


if __name__ == "__main__":
    main()
