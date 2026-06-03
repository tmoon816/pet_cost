"""add discount_amount to cost_records

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-04 14:30:00.000000

为什么：服务订单流水需展示「优惠多少钱」。折后实付存在 amount，
这里单独记会员折扣省下的金额，默认 0，不影响历史订单。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("cost_records", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "discount_amount",
                sa.Numeric(precision=10, scale=2),
                nullable=False,
                server_default="0",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("cost_records", schema=None) as batch_op:
        batch_op.drop_column("discount_amount")
