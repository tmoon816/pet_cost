from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...crud import settings as crud_settings
from ...schemas.settings import TierConfigOut, TierConfigUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/tiers", response_model=TierConfigOut)
def get_tier_config(db: Session = Depends(get_db)):
    """客户分层阈值 + 折扣率。缺配置时回退默认值。"""
    return crud_settings.get_tier_config(db)


@router.put("/tiers", response_model=TierConfigOut)
def update_tier_config(data: TierConfigUpdate, db: Session = Depends(get_db)):
    try:
        return crud_settings.update_tier_config(db, data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
