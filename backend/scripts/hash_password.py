"""生成 bcrypt 密码哈希，复制到 .env 的 ADMIN_PASSWORD_HASH。

用法：
    uv run python scripts/hash_password.py 'your-password'
"""

from __future__ import annotations

import sys
from pathlib import Path

# 让脚本在 backend/scripts/ 下运行也能 import app.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/hash_password.py 'your-password'", file=sys.stderr)
        return 2
    password = sys.argv[1]
    if len(password) < 8:
        print("Password must be at least 8 characters.", file=sys.stderr)
        return 1
    print(hash_password(password))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
