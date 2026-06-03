"""add discount_amount to balance_transactions

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-04 13:30:00.000000

为什么：储值消费时若客户享会员折扣，需把「折扣省下的钱」记进流水，便于对账/复盘。
nullable=False 默认 0，不影响历史记录。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("balance_transactions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "discount_amount",
                sa.Numeric(precision=10, scale=2),
                nullable=False,
                server_default="0",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("balance_transactions", schema=None) as batch_op:
        batch_op.drop_column("discount_amount")
