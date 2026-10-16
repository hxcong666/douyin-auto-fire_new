#!/usr/bin/env bash
# 管理后台脚本公共部分：定位目录、查找 uv
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ADMIN_DIR="$ROOT_DIR/admin"
WEB_DIR="$ADMIN_DIR/web"
LOG_DIR="$ROOT_DIR/logs"
PID_FILE="$LOG_DIR/admin.pid"
UV="$(command -v uv || echo "$HOME/.local/bin/uv")"
[ -x "$UV" ] || { echo "未找到 uv，请先运行 scripts/admin/install.sh" >&2; exit 1; }
mkdir -p "$LOG_DIR"
