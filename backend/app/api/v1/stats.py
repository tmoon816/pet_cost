from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...crud import stats as crud_stats
from ...schemas.stats import (
    StatsByCategory,
    StatsByMonth,
    StatsByPet,
    StatsSummary,
)

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary", response_model=StatsSummary)
def stats_summary(
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
):
    return crud_stats.summary(db, start, end)


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


@router.get("/by-pet", response_model=StatsByPet)
def stats_by_pet(
    customer_id: int | None = None,
    limit: int = Query(5, ge=1, le=100),
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
):
    return crud_stats.by_pet(db, customer_id, limit, start, end)
