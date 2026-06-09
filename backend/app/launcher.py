"""Windows 单机部署入口。

首启时在 exe 同目录建 ``data/app.env`` 写入 JWT 密钥和管理员密码哈希，
之后每次启动只加载 env、跑 alembic 迁移、起 uvicorn。
"""
from __future__ import annotations

import getpass
import os
import secrets
import sys
import webbrowser
from pathlib import Path
from threading import Timer

HOST = "127.0.0.1"
PORT = 8000


def _runtime_dir() -> Path:
    """exe 同目录（frozen），或 backend/（dev）。用来放 data/。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _bundle_dir() -> Path:
    """打包资源目录：alembic.ini / alembic/ / frontend_dist 都在这。"""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def _prompt_password() -> str:
    print("=" * 60)
    print("首次启动：初始化管理员账号（用户名固定 admin）")
    print("=" * 60)
    while True:
        pwd = getpass.getpass("设置登录密码（至少 6 位）: ")
        if len(pwd) < 6:
            print("  密码太短，重来")
            continue
        confirm = getpass.getpass("再输一次确认: ")
        if pwd != confirm:
            print("  两次输入不一致，重来")
            continue
        return pwd


def _ensure_env_file(data_dir: Path) -> Path:
    env_path = data_dir / "app.env"
    if env_path.is_file():
        return env_path

    import bcrypt

    pwd = _prompt_password()
    hashed = bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    secret = secrets.token_urlsafe(48)
    db_path = (data_dir / "pet-cost.db").as_posix()

    env_path.write_text(
        "\n".join(
            [
                "# 自动生成，勿手改。重置密码：删掉本文件重启即可（会同时刷新 JWT 密钥）",
                f"DATABASE_URL=sqlite:///{db_path}",
                "ADMIN_USERNAME=admin",
                f"ADMIN_PASSWORD_HASH={hashed}",
                f"JWT_SECRET_KEY={secret}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"配置已写入 {env_path}\n")
    return env_path


def _load_env(env_path: Path) -> None:
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip()


def _run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    bundle = _bundle_dir()
    cfg = Config(str(bundle / "alembic.ini"))
    cfg.set_main_option("script_location", str(bundle / "alembic"))
    command.upgrade(cfg, "head")


def _open_browser_later(url: str) -> None:
    Timer(1.5, lambda: webbrowser.open(url)).start()


def main() -> None:
    data_dir = _runtime_dir() / "data"
    data_dir.mkdir(exist_ok=True)

    env_path = _ensure_env_file(data_dir)
    _load_env(env_path)

    # 数据库路径始终按运行目录重新计算（绝对路径），不信任 app.env 里存的路径。
    # 这样无论用户把整个文件夹解压/移动到哪里，都能正确找到旁边的 data/pet-cost.db，
    # 也让随包预置的演示数据库可移植。
    os.environ["DATABASE_URL"] = f"sqlite:///{(data_dir / 'pet-cost.db').as_posix()}"

    print(f"数据目录: {data_dir}")
    _run_migrations()

    import uvicorn

    url = f"http://{HOST}:{PORT}"
    print(f"启动完成: {url}（按 Ctrl+C 停止）")
    _open_browser_later(url)

    # 用 import string，避免某些场景下 reload/factory 解析出问题
    uvicorn.run("app.main:app", host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
