from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from ...core.database import get_db
from ...crud import category as crud_category
from ...schemas.category import CategoryCreate, CategoryOut, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return crud_category.list_all(db)


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    return crud_category.create(db, data)


@router.patch("/{code}", response_model=CategoryOut)
def update_category(code: str, data: CategoryUpdate, db: Session = Depends(get_db)):
    obj = crud_category.update(db, code, data)
    if obj is None:
        raise HTTPException(status_code=404, detail="category_not_found")
    return obj


@router.delete("/{code}", status_code=204)
def delete_category(code: str, db: Session = Depends(get_db)):
    if not crud_category.remove(db, code):
        raise HTTPException(status_code=404, detail="category_not_found")
