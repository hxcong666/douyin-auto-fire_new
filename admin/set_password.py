"""交互式设置后台账号密码，写入 .env.admin（权限 600）。密码只保存 scrypt 哈希。"""
from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

from dotenv import set_key

from server.auth.passwords import hash_password
from server.settings import PROJECT_ROOT

MIN_LENGTH = 10


def main() -> int:
    env_file = Path(os.getenv("ADMIN_ENV_FILE", PROJECT_ROOT / ".env.admin"))
    example = PROJECT_ROOT / "admin" / "env.admin.example"
    if not env_file.exists():
        env_file.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
    os.chmod(env_file, 0o600)

    username = input("后台用户名: ").strip()
    if not username:
        print("用户名不能为空", file=sys.stderr)
        return 1
    password = getpass.getpass(f"后台密码（至少 {MIN_LENGTH} 位）: ")
    if len(password) < MIN_LENGTH:
        print(f"密码至少 {MIN_LENGTH} 位", file=sys.stderr)
        return 1
    if getpass.getpass("再次输入密码: ") != password:
        print("两次输入的密码不一致", file=sys.stderr)
        return 1

    set_key(env_file, "ADMIN_USERNAME", username, quote_mode="never")
    set_key(env_file, "ADMIN_PASSWORD_HASH", hash_password(password), quote_mode="never")
    os.chmod(env_file, 0o600)
    print(f"已保存到 {env_file}，重启后台后生效")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
