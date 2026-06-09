"""add recharge_packages table + seed default tiers

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-04 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recharge_packages",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("subtitle", sa.String(length=100), nullable=True),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("bonus_amount", sa.Numeric(precision=10, scale=2), server_default="0", nullable=False),
        sa.Column("gifts", sa.JSON(), nullable=False),
        sa.Column("highlights", sa.JSON(), nullable=False),
        sa.Column("badge", sa.String(length=20), nullable=True),
        sa.Column("is_recommended", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    # 种子：基础 / Pro / Max 三档默认套餐
    packages = sa.table(
        "recharge_packages",
        sa.column("name", sa.String),
        sa.column("subtitle", sa.String),
        sa.column("price", sa.Numeric),
        sa.column("bonus_amount", sa.Numeric),
        sa.column("gifts", sa.JSON),
        sa.column("highlights", sa.JSON),
        sa.column("badge", sa.String),
        sa.column("is_recommended", sa.Boolean),
        sa.column("is_active", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(
        packages,
        [
            {
                "name": "基础卡",
                "subtitle": "轻度到店，先充先享",
                "price": 500,
                "bonus_amount": 50,
                "gifts": ["宠物零食 1 包"],
                "highlights": ["充 500 送 50", "余额永久有效", "全项目通用"],
                "badge": None,
                "is_recommended": False,
                "is_active": True,
                "sort_order": 10,
            },
            {
                "name": "Pro 卡",
                "subtitle": "常来洗护，超值之选",
                "price": 1000,
                "bonus_amount": 200,
                "gifts": ["精细洗护 1 次", "进口猫砂 1 袋"],
                "highlights": ["充 1000 送 200", "洗护 9 折", "生日双倍积分", "专属顾问"],
                "badge": "最受欢迎",
                "is_recommended": True,
                "is_active": True,
                "sort_order": 20,
            },
            {
                "name": "Max 卡",
                "subtitle": "重度玩家，至尊礼遇",
                "price": 2000,
                "bonus_amount": 600,
                "gifts": ["全套 SPA 2 次", "进口主粮 1 袋", "宠物玩具礼盒"],
                "highlights": ["充 2000 送 600", "全项目 8.5 折", "免费寄养 2 晚/年", "专属顾问 + 优先预约"],
                "badge": "超值",
                "is_recommended": False,
                "is_active": True,
                "sort_order": 30,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("recharge_packages")
