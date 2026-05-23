from typing import List, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..models import Customer, CostRecord, Pet
from ..schemas.pet import PetCreate, PetUpdate


def get(db: Session, pet_id: int) -> Pet | None:
    return db.get(Pet, pet_id)


def list_paginated(
    db: Session,
    customer_id: int | None,
    page: int,
    page_size: int,
    q: str | None = None,
) -> Tuple[List[dict], int]:
    """列出宠物，并以 dict 形式返回，额外包含 last_visit_at（MAX(cost_records.occurred_on)）
    和 customer_name（前端列表只展示 ID 太抽象，要主人姓名直观一些）。

    支持 q 跨字段搜索：宠物名 / 宠物拼音 / 主人名 / 主人拼音 / 主人手机号。

    返回 dict 而非 ORM 实例是为了后接 PetListItem 这个非 from_attributes 映射也能顺利序列化。
    """
    last_visit_subq = (
        select(func.max(CostRecord.occurred_on))
        .where(CostRecord.pet_id == Pet.id)
        .correlate(Pet)
        .scalar_subquery()
    )

    stmt = select(Pet, last_visit_subq.label("last_visit_at"), Customer.name.label("customer_name")).join(
        Customer, Customer.id == Pet.customer_id
    )
    count_stmt = select(func.count(Pet.id)).join(Customer, Customer.id == Pet.customer_id)
    if customer_id is not None:
        stmt = stmt.where(Pet.customer_id == customer_id)
        count_stmt = count_stmt.where(Pet.customer_id == customer_id)
    if q and q.strip():
        like = f"%{q.strip()}%"
        cond = or_(
            Pet.name.like(like),
            Pet.name_pinyin.like(like),
            Pet.name_initials.like(like),
            Customer.name.like(like),
            Customer.name_pinyin.like(like),
            Customer.name_initials.like(like),
            Customer.phone.like(like),
        )
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    stmt = stmt.order_by(Pet.id.desc()).offset((page - 1) * page_size).limit(page_size)

    rows = db.execute(stmt).all()
    items: List[dict] = []
    for pet, last_visit_at, customer_name in rows:
        item = {
            "id": pet.id,
            "customer_id": pet.customer_id,
            "customer_name": customer_name,
            "name": pet.name,
            "species": pet.species,
            "breed": pet.breed,
            "gender": pet.gender,
            "birthday": pet.birthday,
            "note": pet.note,
            "created_at": pet.created_at,
            "updated_at": pet.updated_at,
            "last_visit_at": last_visit_at,
        }
        items.append(item)
    total = int(db.scalar(count_stmt) or 0)
    return items, total


def _customer_exists(db: Session, customer_id: int) -> bool:
    return db.scalar(select(Customer.id).where(Customer.id == customer_id)) is not None


def create(db: Session, data: PetCreate) -> Pet | None:
    if not _customer_exists(db, data.customer_id):
        return None
    obj = Pet(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, pet_id: int, data: PetUpdate) -> Pet | None:
    obj = db.get(Pet, pet_id)
    if obj is None:
        return None
    payload = data.model_dump(exclude_unset=True)
    if "customer_id" in payload and not _customer_exists(db, payload["customer_id"]):
        return None
    for field, value in payload.items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def remove(db: Session, pet_id: int) -> bool:
    obj = db.get(Pet, pet_id)
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True
