"""寄养按天扣费调度。

触发策略（单机版，无外部调度器）：
  - 应用启动时立即结算一次（补扣关机期间欠下的天数）。
  - 之后每隔 SETTLE_INTERVAL_SECONDS 再结算一次（默认 1 小时），覆盖跨天。

并发安全：用一把进程内锁串行化，避免启动结算与定时结算撞车导致重复处理。
结算引擎本身幂等（游标 + 唯一约束），即使锁失效也不会重复扣费。
"""
from __future__ import annotations

import logging
import threading

from ..crud import boarding as crud_boarding
from .database import SessionLocal

logger = logging.getLogger("boarding")

SETTLE_INTERVAL_SECONDS = 3600  # 每小时跑一次，跨天即结算

_lock = threading.Lock()
_timer: threading.Timer | None = None
_stopped = False


def run_settlement_once() -> dict:
    """结算所有在住寄养单到今天。串行执行，吞掉异常只记日志，绝不影响主流程。"""
    with _lock:
        db = SessionLocal()
        try:
            result = crud_boarding.settle_all_active(db)
            if result["days_charged"] > 0 or result["errors"]:
                logger.info(
                    "boarding settled: %s orders, %s day(s) charged, errors=%s",
                    result["orders_processed"], result["days_charged"], result["errors"],
                )
            return result
        except Exception:  # noqa: BLE001
            logger.exception("boarding settlement failed")
            return {"orders_processed": 0, "days_charged": 0, "errors": []}
        finally:
            db.close()


def _tick() -> None:
    if _stopped:
        return
    run_settlement_once()
    _schedule_next()


def _schedule_next() -> None:
    global _timer
    if _stopped:
        return
    _timer = threading.Timer(SETTLE_INTERVAL_SECONDS, _tick)
    _timer.daemon = True
    _timer.start()


def start() -> None:
    """启动时调用：先立即结算一次，再排下一次定时。"""
    global _stopped
    _stopped = False
    run_settlement_once()
    _schedule_next()


def stop() -> None:
    global _stopped
    _stopped = True
    if _timer is not None:
        _timer.cancel()
