#!/usr/bin/env bash
# 安装 uv（如未安装）和后台 Python 依赖。依赖装在独立的 admin/.venv，不影响续火花程序的环境。
# 服务器上请以运行用户执行：sudo -u douyin-sender -H scripts/admin/install.sh
set -euo pipefail
if ! command -v uv >/dev/null && [ ! -x "$HOME/.local/bin/uv" ]; then
  curl -LsSf https://astral.sh/uv/0.9.5/install.sh | env UV_NO_MODIFY_PATH=1 sh
fi
source "$(dirname "$0")/_common.sh"
cd "$ADMIN_DIR"
"$UV" sync --frozen --no-dev
echo "后台依赖安装完成"
