"""日志同时输出到控制台和 logs/admin.log（按天轮转，保留 14 天）。"""
from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def configure_logging(logs_dir: Path) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    file_handler = TimedRotatingFileHandler(logs_dir / "admin.log", when="midnight", backupCount=14, encoding="utf-8")
    console = logging.StreamHandler()
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)
    for handler in (file_handler, console):
        handler.setFormatter(formatter)
        root.addHandler(handler)
    # uvicorn 访问日志会记录请求路径，不含 Cookie 和请求体
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).handlers.clear()
        logging.getLogger(name).propagate = True
