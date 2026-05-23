"""全局搜索 schema。"""

from pydantic import BaseModel


class SearchResult(BaseModel):
    type: str      # customer / pet / cost
    id: int
    title: str
    subtitle: str
    url: str
    score: int = 0


class SearchResponse(BaseModel):
    results: list[SearchResult]