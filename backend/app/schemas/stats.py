from datetime import date
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


class StatsCustomerAcquisition(BaseModel):
    """T-009: 本月新客 vs 回头客。total = new + returning。"""

    year: int
    month: int
    new_customers: int
    returning_customers: int
    total: int


class StatsDormantCustomerItem(BaseModel):
    """T-010: 久未到店老客预警项。"""

    customer_id: int
    customer_name: str
    last_visit_at: date
    days_since: int
    phone: str = ""


class StatsTopCustomerItem(BaseModel):
    """T-026: 高价值客户 Top N。"""

    rank: int
    customer_id: int
    customer_name: str
    total_amount: Decimal
    order_count: int


StatsDormantCustomers = List[StatsDormantCustomerItem]
StatsTopCustomers = List[StatsTopCustomerItem]

