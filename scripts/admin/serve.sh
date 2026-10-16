#!/usr/bin/env bash
# 前台运行管理后台（调试或 systemd 使用），Ctrl+C 退出；日志同时写入 logs/admin.log
source "$(dirname "$0")/_common.sh"
cd "$ADMIN_DIR"
exec "$UV" run --frozen --no-dev python main.py
