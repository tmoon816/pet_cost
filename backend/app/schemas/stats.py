from decimal import Decimal
from typing import List

from pydantic import BaseModel


class StatsSummary(BaseModel):
    total_amount: Decimal
    record_count: int
    customer_count: int
    pet_count: int


class StatsByCategoryItem(BaseModel):
    category: str
    label: str
    total: Decimal
    count: int


class StatsByMonthItem(BaseModel):
    month: str
    total: Decimal


class StatsByPetItem(BaseModel):
    pet_id: int
    pet_name: str
    total: Decimal


StatsByCategory = List[StatsByCategoryItem]
StatsByMonth = List[StatsByMonthItem]
StatsByPet = List[StatsByPetItem]
