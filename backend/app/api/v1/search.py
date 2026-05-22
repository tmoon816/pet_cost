from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...crud import search as crud_search
from ...schemas.search import SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
def search(
    q: str = Query("", max_length=200),
    db: Session = Depends(get_db),
):
    """全局搜索：扫客户 name/phone、宠物 name、消费记录 note。"""
    results = crud_search.search(db, q)
    return {"results": results}