from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...crud import customer as crud_customer
from ...crud import recharge_package as crud_pkg
from ...schemas.recharge_package import (
    PackageCheckoutRequest,
    PackageCheckoutResult,
    RechargePackageCreate,
    RechargePackageOut,
    RechargePackageUpdate,
)

router = APIRouter(prefix="/recharge-packages", tags=["recharge-packages"])


@router.get("", response_model=list[RechargePackageOut])
def list_packages(
    active_only: bool = Query(False, description="只返回启用中的套餐"),
    db: Session = Depends(get_db),
):
    return crud_pkg.list_all(db, active_only=active_only)


@router.post("", response_model=RechargePackageOut, status_code=201)
def create_package(data: RechargePackageCreate, db: Session = Depends(get_db)):
    return crud_pkg.create(db, data)


@router.patch("/{package_id}", response_model=RechargePackageOut)
def update_package(package_id: int, data: RechargePackageUpdate, db: Session = Depends(get_db)):
    obj = crud_pkg.update(db, package_id, data)
    if obj is None:
        raise HTTPException(status_code=404, detail="package_not_found")
    return obj


@router.delete("/{package_id}", status_code=204)
def delete_package(package_id: int, db: Session = Depends(get_db)):
    if not crud_pkg.remove(db, package_id):
        raise HTTPException(status_code=404, detail="package_not_found")


@router.post("/{package_id}/checkout", response_model=PackageCheckoutResult)
def checkout_package(
    package_id: int, data: PackageCheckoutRequest, db: Session = Depends(get_db)
):
    """按套餐给客户充值：到账 = 本金 + 赠送，赠品记入流水备注。"""
    package = crud_pkg.get(db, package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="package_not_found")
    if not package.is_active:
        raise HTTPException(status_code=400, detail="package_inactive")
    customer = crud_customer.get(db, data.customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="customer_not_found")

    customer, txn = crud_pkg.checkout(
        db, package, customer, channel=data.channel, note=data.note
    )
    return {
        "customer_id": customer.id,
        "customer_name": customer.name,
        "package_id": package.id,
        "package_name": package.name,
        "paid_amount": package.price,
        "bonus_amount": package.bonus_amount,
        "credited": package.price + package.bonus_amount,
        "gifts": list(package.gifts or []),
        "balance": customer.balance,
        "transaction_id": txn.id,
    }
