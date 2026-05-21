from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...crud import cost as crud_cost
from ...models import CostCategory, Pet
from ...schemas.common import Page
from ...schemas.cost import CostCreate, CostOut, CostUpdate

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
