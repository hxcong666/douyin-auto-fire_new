#!/usr/bin/env bash
# 后台方式启动管理后台；服务器上推荐用 systemd（见 deploy/systemd/douyin-admin.service）
source "$(dirname "$0")/_common.sh"
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "管理后台已在运行 (pid $(cat "$PID_FILE"))"; exit 0
fi
cd "$ADMIN_DIR"
nohup "$UV" run --frozen --no-dev python main.py >>"$LOG_DIR/admin.out" 2>&1 &
echo $! >"$PID_FILE"
sleep 2
kill -0 "$(cat "$PID_FILE")" 2>/dev/null || { echo "启动失败，查看 $LOG_DIR/admin.out" >&2; exit 1; }
echo "管理后台已启动 (pid $(cat "$PID_FILE"))，日志: $LOG_DIR/admin.log"
