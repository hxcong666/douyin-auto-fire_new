#!/usr/bin/env bash
# 运行续火花程序自身的测试（使用项目根目录 .venv）
set -euo pipefail
cd "$(dirname "$0")/.."
UV="$(command -v uv || echo "$HOME/.local/bin/uv")"
if [ ! -x .venv/bin/python ]; then
  "$UV" venv -q .venv
  "$UV" pip install -q --python .venv/bin/python -r requirements-dev.txt
fi
exec .venv/bin/python -m pytest -q -p no:cacheprovider "$@"
