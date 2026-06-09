import sys
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api.v1 import auth, boarding, budgets, categories, costs, customers, pets, recharge_packages, search, settings as settings_api, stats
from .core.auth import get_current_admin
from .core.config import settings
from .core.exceptions import ConflictError, InsufficientBalanceError

app = FastAPI(title="Pet Cost API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": exc.detail})


@app.exception_handler(InsufficientBalanceError)
async def insufficient_balance_handler(request: Request, exc: InsufficientBalanceError):
    return JSONResponse(status_code=400, content={"detail": exc.detail})


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.on_event("startup")
def _start_boarding_scheduler() -> None:
    """启动时结算寄养欠费 + 起每日定时。失败不阻断应用启动。"""
    try:
        from .core import boarding_scheduler
        boarding_scheduler.start()
    except Exception:  # noqa: BLE001
        import logging
        logging.getLogger("boarding").exception("failed to start boarding scheduler")


@app.on_event("shutdown")
def _stop_boarding_scheduler() -> None:
    try:
        from .core import boarding_scheduler
        boarding_scheduler.stop()
    except Exception:  # noqa: BLE001
        pass


# auth 路由不能加守卫，否则连登录都进不去
app.include_router(auth.router, prefix="/api/v1")

# 其余业务路由统一挂全局 JWT 守卫
for module in (budgets, categories, costs, customers, pets, recharge_packages, search, settings_api, stats, boarding):
    app.include_router(
        module.router,
        prefix="/api/v1",
        dependencies=[Depends(get_current_admin)],
    )


# 单机部署：把前端 dist 挂到根路径
def _resolve_frontend_dist() -> Path | None:
    # PyInstaller 打包后：通过 _MEIPASS 解压到临时目录
    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", ""))
        bundled = meipass / "frontend_dist"
        if bundled.is_dir():
            return bundled
    # 开发模式：backend/../frontend/dist
    repo_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if repo_dist.is_dir():
        return repo_dist
    return None


class SPAStaticFiles(StaticFiles):
    """SPA 路由兜底：未命中静态文件且不是 /api 请求时回退到 index.html。"""

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404 and not path.startswith("api/"):
                return await super().get_response("index.html", scope)
            raise


_frontend_dist = _resolve_frontend_dist()
if _frontend_dist is not None:
    app.mount("/", SPAStaticFiles(directory=str(_frontend_dist), html=True), name="spa")
