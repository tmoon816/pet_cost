from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.exceptions import ConflictError
from ..models import CostCategory, CostRecord
from ..schemas.category import CategoryCreate, CategoryUpdate


def get(db: Session, code: str) -> CostCategory | None:
    return db.get(CostCategory, code)


def list_all(db: Session) -> List[CostCategory]:
    stmt = select(CostCategory).order_by(CostCategory.sort_order, CostCategory.code)
    return list(db.scalars(stmt).all())


def create(db: Session, data: CategoryCreate) -> CostCategory:
    if db.get(CostCategory, data.code) is not None:
        raise ConflictError({"detail": "category_code_exists", "code": data.code})
    obj = CostCategory(code=data.code, label=data.label, sort_order=data.sort_order)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, code: str, data: CategoryUpdate) -> CostCategory | None:
    obj = db.get(CostCategory, code)
    if obj is None:
        return None
    payload = data.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def remove(db: Session, code: str) -> bool:
    obj = db.get(CostCategory, code)
    if obj is None:
        return False
    in_use = db.scalar(
        select(CostRecord.id).where(CostRecord.category_code == code).limit(1)
    )
    if in_use is not None:
        raise ConflictError({"detail": "category_in_use", "code": code})
    db.delete(obj)
    db.commit()
    return True
