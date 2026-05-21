from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...crud import pet as crud_pet
from ...schemas.common import Page
from ...schemas.pet import PetCreate, PetOut, PetUpdate

router = APIRouter(prefix="/pets", tags=["pets"])


@router.get("", response_model=Page[PetOut])
def list_pets(
    customer_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = crud_pet.list_paginated(db, customer_id=customer_id, page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{pet_id}", response_model=PetOut)
def get_pet(pet_id: int, db: Session = Depends(get_db)):
    obj = crud_pet.get(db, pet_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="pet_not_found")
    return obj


@router.post("", response_model=PetOut, status_code=201)
def create_pet(data: PetCreate, db: Session = Depends(get_db)):
    obj = crud_pet.create(db, data)
    if obj is None:
        raise HTTPException(status_code=404, detail="customer_not_found")
    return obj


@router.patch("/{pet_id}", response_model=PetOut)
def update_pet(pet_id: int, data: PetUpdate, db: Session = Depends(get_db)):
    existing = crud_pet.get(db, pet_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="pet_not_found")
    obj = crud_pet.update(db, pet_id, data)
    if obj is None:
        raise HTTPException(status_code=404, detail="customer_not_found")
    return obj


@router.delete("/{pet_id}", status_code=204)
def delete_pet(pet_id: int, db: Session = Depends(get_db)):
    if not crud_pet.remove(db, pet_id):
        raise HTTPException(status_code=404, detail="pet_not_found")
