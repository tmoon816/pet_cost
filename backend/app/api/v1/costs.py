from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...crud import cost as crud_cost
from ...crud.export_csv import costs_csv
from ...models import CostCategory, Pet
from ...schemas.common import Page
from ...schemas.cost import CostBatchCreate, CostCreate, CostOut, CostUpdate

router = APIRouter(prefix="/costs", tags=["costs"])


@router.get("", response_model=Page[CostOut])
def list_costs(
    pet_id: int | None = None,
    customer_id: int | None = None,
    category: str | None = Query(None, alias="category"),
    start: date | None = None,
    end: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = crud_cost.list_paginated(
        db,
        pet_id=pet_id,
        customer_id=customer_id,
        category_code=category,
        start=start,
        end=end,
        page=page,
        page_size=page_size,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/export")
def export_costs(
    pet_id: int | None = None,
    customer_id: int | None = None,
    category: str | None = Query(None, alias="category"),
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
):
    """T-022：导出消费记录为 CSV（UTF-8 BOM）。"""
    from app.models import Customer

    items, _ = crud_cost.list_paginated(
        db,
        pet_id=pet_id,
        customer_id=customer_id,
        category_code=category,
        start=start,
        end=end,
        page=1,
        page_size=99999,
    )
    # 补客户名和分类 label
    rows: list[dict] = []
    for item in items:
        pet = db.get(Pet, item.pet_id)
        customer_name = ""
        if pet and pet.customer_id:
            c = db.get(Customer, pet.customer_id)
            customer_name = c.name if c else ""
        cat = db.get(CostCategory, item.category_code)
        category_label = cat.label if cat else item.category_code
        rows.append({
            "occurred_on": item.occurred_on,
            "pet_name": getattr(item, "pet_name", ""),
            "customer_name": customer_name,
            "category_label": category_label,
            "amount": item.amount,
            "discount_amount": getattr(item, "discount_amount", 0),
            "pay_method": item.pay_method,
            "note": item.note,
        })
    return costs_csv(rows)


@router.get("/{cost_id}", response_model=CostOut)
def get_cost(cost_id: int, db: Session = Depends(get_db)):
    obj = crud_cost.get(db, cost_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="cost_not_found")
    return obj


def _validate_refs(db: Session, pet_id: int | None, category_code: str | None):
    if pet_id is not None and db.get(Pet, pet_id) is None:
        raise HTTPException(status_code=404, detail="pet_not_found")
    if category_code is not None and db.get(CostCategory, category_code) is None:
        raise HTTPException(status_code=404, detail="category_not_found")


@router.post("", response_model=CostOut, status_code=201)
def create_cost(data: CostCreate, db: Session = Depends(get_db)):
    _validate_refs(db, data.pet_id, data.category_code)
    obj = crud_cost.create(db, data)
    if obj is None:
        raise HTTPException(status_code=404, detail="reference_not_found")
    return obj


@router.post("/batch", response_model=list[CostOut], status_code=201)
def create_costs_batch(data: CostBatchCreate, db: Session = Depends(get_db)):
    """T-029: 同金额同分类同日期，给多只宠物批量开单。事务原子，任一引用错全部回滚。"""
    if db.get(CostCategory, data.category_code) is None:
        raise HTTPException(status_code=404, detail="category_not_found")
    # 去重避免同一只宠物被插两条
    unique_pet_ids = list(dict.fromkeys(data.pet_ids))
    for pid in unique_pet_ids:
        if db.get(Pet, pid) is None:
            raise HTTPException(status_code=404, detail="pet_not_found")
    data.pet_ids = unique_pet_ids
    return crud_cost.create_batch(db, data)


@router.patch("/{cost_id}", response_model=CostOut)
def update_cost(cost_id: int, data: CostUpdate, db: Session = Depends(get_db)):
    if crud_cost.get(db, cost_id) is None:
        raise HTTPException(status_code=404, detail="cost_not_found")
    payload = data.model_dump(exclude_unset=True)
    _validate_refs(db, payload.get("pet_id"), payload.get("category_code"))
    obj = crud_cost.update(db, cost_id, data)
    if obj is None:
        raise HTTPException(status_code=404, detail="reference_not_found")
    return obj


@router.delete("/{cost_id}", status_code=204)
def delete_cost(cost_id: int, db: Session = Depends(get_db)):
    if not crud_cost.remove(db, cost_id):
        raise HTTPException(status_code=404, detail="cost_not_found")
