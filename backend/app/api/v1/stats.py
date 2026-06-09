from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...crud import stats as crud_stats
from ...schemas.stats import (
    StatsByCategory,
    StatsByDay,
    StatsByMonth,
    StatsByPet,
    StatsCashflow,
    StatsCustomerAcquisition,
    StatsDormantCustomers,
    StatsSummary,
    StatsTopCustomerItem,
    StatsTopCustomers,
)

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary", response_model=StatsSummary)
def stats_summary(
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
):
    return crud_stats.summary(db, start, end)


@router.get("/cashflow", response_model=StatsCashflow)
def stats_cashflow(
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
):
    """实收口径（现金流入）：充值本金 + 现金消费。与营业额（服务发生）互补。"""
    return crud_stats.cashflow(db, start, end)


@router.get("/by-category", response_model=StatsByCategory)
def stats_by_category(
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
):
    return crud_stats.by_category(db, start, end)


@router.get("/by-month", response_model=StatsByMonth)
def stats_by_month(
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
):
    return crud_stats.by_month(db, start, end)


@router.get("/by-day", response_model=StatsByDay)
def stats_by_day(
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
):
    """按天聚合营业额。Dashboard 营业额卡片下方迷你趋势用，跟随日期区间。"""
    return crud_stats.by_day(db, start, end)


@router.get("/by-pet", response_model=StatsByPet)
def stats_by_pet(
    customer_id: int | None = None,
    limit: int = Query(5, ge=1, le=100),
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
):
    return crud_stats.by_pet(db, customer_id, limit, start, end)


@router.get("/customer-acquisition", response_model=StatsCustomerAcquisition)
def stats_customer_acquisition(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
):
    """T-009: 某年某月的新客 vs 回头客。"""
    return crud_stats.customer_acquisition(db, year, month)


@router.get("/dormant-customers", response_model=StatsDormantCustomers)
def stats_dormant_customers(
    days: int = Query(90, ge=1, le=3650),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """T-010: 返回距今 ≥ days 天未到店的老客，按 last_visit_at 升序。"""
    return crud_stats.dormant_customers(db, days, limit)


@router.get("/top-customers", response_model=StatsTopCustomers)
def stats_top_customers(
    limit: int = Query(10, ge=1, le=50),
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
):
    """T-026: 按消费金额返回 Top N 高价值客户。传 start/end 则按区间（如本月）统计。"""
    return crud_stats.top_customers(db, limit, start, end)
