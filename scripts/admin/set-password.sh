#!/usr/bin/env bash
# 设置后台登录账号和密码（交互式），写入项目根目录 .env.admin
source "$(dirname "$0")/_common.sh"
cd "$ADMIN_DIR"
exec "$UV" run --frozen --no-dev python set_password.py
