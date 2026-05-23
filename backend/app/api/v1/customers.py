from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...crud import customer as crud_customer
from ...crud import import_customers as crud_import
from ...crud.export_csv import customers_csv
from ...schemas.common import Page
from ...schemas.customer import CustomerCreate, CustomerListItem, CustomerOut, CustomerSummary, CustomerUpdate, CustomerWithPets

router = APIRouter(prefix="/customers", tags=["customers"])


MAX_IMPORT_BYTES = 2 * 1024 * 1024  # 2MB，门店量级足够


def _read_xlsx(file: UploadFile) -> bytes:
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="must_be_xlsx")
    data = file.file.read()
    if len(data) > MAX_IMPORT_BYTES:
        raise HTTPException(status_code=400, detail="file_too_large")
    if not data:
        raise HTTPException(status_code=400, detail="empty_file")
    return data


@router.get("", response_model=Page[CustomerListItem])
def list_customers(
    q: str | None = None,
    sort_by: str | None = Query(None, pattern="^(total_amount|created_at)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = crud_customer.list_paginated(
        db, q=q, page=page, page_size=page_size, sort_by=sort_by, sort_dir=sort_dir
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/recent", response_model=list[CustomerOut])
def list_recent_customers(
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """T-014：按「名下最近一次消费」倒序返回最近消费过的客户。无消费不返回。"""
    return crud_customer.list_recent(db, limit=limit)


@router.get("/export")
def export_customers(
    q: str | None = None,
    sort_by: str | None = Query(None, pattern="^(total_amount|created_at)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """T-022：导出客户列表为 CSV（UTF-8 BOM）。"""
    items, _ = crud_customer.list_paginated(
        db, q=q, page=1, page_size=99999, sort_by=sort_by, sort_dir=sort_dir
    )
    return customers_csv(items)


@router.get("/import/template")
def download_import_template():
    """下载批量导入 xlsx 模板（含表头 + 示例行 + 填写说明）。"""
    data = crud_import.build_template()
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=customer_import_template.xlsx"},
    )


@router.post("/import/preview")
def preview_import_customers(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """dry-run：解析 + 校验，不写库。返回 {ok, errors, total}。"""
    data = _read_xlsx(file)
    return crud_import.preview(db, data)


@router.post("/import/commit")
def commit_import_customers(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """正式写库。若仍有任何错误则整批拒绝（原子性），返回 errors。"""
    data = _read_xlsx(file)
    return crud_import.commit(db, data)


@router.get("/{customer_id}", response_model=CustomerWithPets)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    obj = crud_customer.get_with_pets(db, customer_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="customer_not_found")
    return obj


@router.get("/{customer_id}/summary", response_model=CustomerSummary)
def get_customer_summary(customer_id: int, db: Session = Depends(get_db)):
    """T-007：详情页聚合卡片（累计消费 / 上次到店 / 总订单数）。"""
    summary = crud_customer.get_summary(db, customer_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="customer_not_found")
    return summary


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    return crud_customer.create(db, data)


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: int, data: CustomerUpdate, db: Session = Depends(get_db)):
    obj = crud_customer.update(db, customer_id, data)
    if obj is None:
        raise HTTPException(status_code=404, detail="customer_not_found")
    return obj


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    if not crud_customer.remove(db, customer_id):
        raise HTTPException(status_code=404, detail="customer_not_found")
