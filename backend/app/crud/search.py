"""全局搜索：按 q 扫 customer name/phone、pet name、cost note 返回混合结果。

支持中文姓名拼音首字母 / 全拼输入（依赖 customers.name_pinyin/name_initials 和
pets.name_pinyin/name_initials 由 ORM 写入时自动生成 + alembic 历史回填）。
"""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import CostRecord, Customer, Pet


def _score(text: str | None, q: str) -> int:
    """精确=100，前缀=50，子串=10，无命中=0。大小写不敏感。"""
    if not text or not q:
        return 0
    t = text.lower()
    qq = q.lower()
    if t == qq:
        return 100
    if t.startswith(qq):
        return 50
    if qq in t:
        return 10
    return 0


def search(db: Session, q: str, per_group: int = 5) -> list[dict]:
    if not q or not q.strip():
        return []

    qs = q.strip()
    like = f"%{qs}%"

    # 客户：name / phone / name_pinyin / name_initials 都纳入 OR
    cust_rows = db.execute(
        select(
            Customer.id,
            Customer.name,
            Customer.phone,
            Customer.name_pinyin,
            Customer.name_initials,
        )
        .where(
            or_(
                Customer.name.like(like),
                Customer.phone.like(like),
                Customer.name_pinyin.like(like),
                Customer.name_initials.like(like),
            )
        )
        .order_by(Customer.name)
        .limit(per_group * 4),
    ).all()

    # 宠物：name / name_pinyin / name_initials
    pet_rows = db.execute(
        select(
            Pet.id,
            Pet.name,
            Pet.species,
            Pet.breed,
            Pet.name_pinyin,
            Pet.name_initials,
            Customer.name.label("owner_name"),
        )
        .join(Pet.customer)
        .where(
            or_(
                Pet.name.like(like),
                Pet.name_pinyin.like(like),
                Pet.name_initials.like(like),
            )
        )
        .order_by(Pet.name)
        .limit(per_group * 4),
    ).all()

    # 消费记录（note 不做拼音化，意义不大）
    cost_rows = db.execute(
        select(
            CostRecord.id,
            CostRecord.amount,
            CostRecord.occurred_on,
            CostRecord.note,
            Pet.name.label("pet_name"),
        )
        .join(CostRecord.pet)
        .where(CostRecord.note.like(like))
        .order_by(CostRecord.occurred_on.desc())
        .limit(per_group * 4),
    ).all()

    customers: list[dict] = []
    for row in cust_rows:
        score = max(
            _score(row.name, qs),
            _score(row.phone, qs),
            _score(row.name_pinyin, qs),
            _score(row.name_initials, qs),
        )
        customers.append({
            "type": "customer",
            "id": row.id,
            "title": row.name,
            "subtitle": row.phone or "",
            "url": f"/customers/{row.id}",
            "score": score,
        })

    pets: list[dict] = []
    for row in pet_rows:
        breed_tag = f" · {row.breed}" if row.breed else ""
        species = {"dog": "🐶", "cat": "🐱"}.get(row.species, "🐾")
        pets.append({
            "type": "pet",
            "id": row.id,
            "title": f"{species} {row.name}",
            "subtitle": f"{row.breed or row.species}{breed_tag} · 主人: {row.owner_name}" if row.owner_name else (row.breed or row.species),
            "url": f"/pets/{row.id}",
            "score": max(
                _score(row.name, qs),
                _score(row.name_pinyin, qs),
                _score(row.name_initials, qs),
            ),
        })

    costs: list[dict] = []
    for row in cost_rows:
        pet_label = f" · {row.pet_name}" if row.pet_name else ""
        note_snippet = row.note[:20] if row.note else ""
        costs.append({
            "type": "cost",
            "id": row.id,
            "title": f"¥{float(row.amount):.2f} {note_snippet}",
            "subtitle": f"{row.occurred_on}{pet_label}",
            "url": "/bills",
            "score": _score(row.note, qs),
        })

    # 组内按 score desc 排序；按 type 顺序拼接
    customers.sort(key=lambda r: r["score"], reverse=True)
    pets.sort(key=lambda r: r["score"], reverse=True)
    costs.sort(key=lambda r: r["score"], reverse=True)

    return customers[:per_group] + pets[:per_group] + costs[:per_group]
