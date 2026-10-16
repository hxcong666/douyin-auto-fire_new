#!/usr/bin/env bash
# 停止由 start.sh 启动的管理后台
source "$(dirname "$0")/_common.sh"
if [ ! -f "$PID_FILE" ] || ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "管理后台未在运行"; rm -f "$PID_FILE"; exit 0
fi
kill "$(cat "$PID_FILE")" && rm -f "$PID_FILE"
echo "管理后台已停止"
