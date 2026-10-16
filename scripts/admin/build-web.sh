#!/usr/bin/env bash
# 构建前端静态文件到 admin/web/out
source "$(dirname "$0")/_common.sh"
cd "$WEB_DIR"
npm ci
npm run build
echo "前端已构建到 $WEB_DIR/out"
