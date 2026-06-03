"""add customer balance, cost pay_method, and balance_transactions

Revision ID: a1b2c3d4e5f6
Revises: 9b2e1f3a5c10
Create Date: 2026-06-04 10:00:00.000000

为什么：储值功能。
- customers.balance：当前储值余额（含赠送），默认 0，不破坏现有客户。
- cost_records.pay_method：订单支付方式 balance/cash，历史数据默认 cash（现金，不动余额）。
- balance_transactions：储值流水账本（充值/消费/退款/调整），每笔留痕 + 余额快照，可对账。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "9b2e1f3a5c10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("customers", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "balance",
                sa.Numeric(precision=10, scale=2),
                nullable=False,
                server_default="0",
            )
        )

    with op.batch_alter_table("cost_records", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "pay_method",
                sa.String(length=20),
                nullable=False,
                server_default="cash",
            )
        )

    op.create_table(
        "balance_transactions",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=False),
        sa.Column(
            "customer_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            nullable=False,
        ),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "bonus_amount",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            server_default="0",
        ),
        sa.Column("balance_after", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=True),
        sa.Column("cost_id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_baltxn_customer", "balance_transactions", ["customer_id"])
    op.create_index("idx_baltxn_created", "balance_transactions", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_baltxn_created", table_name="balance_transactions")
    op.drop_index("idx_baltxn_customer", table_name="balance_transactions")
    op.drop_table("balance_transactions")

    with op.batch_alter_table("cost_records", schema=None) as batch_op:
        batch_op.drop_column("pay_method")

    with op.batch_alter_table("customers", schema=None) as batch_op:
        batch_op.drop_column("balance")
