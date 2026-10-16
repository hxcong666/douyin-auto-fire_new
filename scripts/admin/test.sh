#!/usr/bin/env bash
# 运行管理后台测试（含与续火花程序配置解析的联合校验）
source "$(dirname "$0")/_common.sh"
cd "$ADMIN_DIR"
exec "$UV" run --frozen python -m pytest -q tests -p no:cacheprovider "$@"
