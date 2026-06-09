"""add boarding_orders + cost_records.boarding_order_id with unique day guard

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "boarding_orders",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, nullable=False),
        sa.Column("pet_id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=False),
        sa.Column("customer_id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=False),
        sa.Column("check_in_date", sa.Date(), nullable=False),
        sa.Column("expected_days", sa.Integer(), nullable=False),
        sa.Column("daily_rate", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("check_out_date", sa.Date(), nullable=True),
        sa.Column("settled_through", sa.Date(), nullable=True),
        sa.Column("total_charged", sa.Numeric(precision=10, scale=2), server_default="0", nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["pet_id"], ["pets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    with op.batch_alter_table("boarding_orders", schema=None) as batch_op:
        batch_op.create_index("idx_boarding_pet", ["pet_id"], unique=False)
        batch_op.create_index("idx_boarding_customer", ["customer_id"], unique=False)
        batch_op.create_index("idx_boarding_status", ["status"], unique=False)

    # cost_records 加 boarding_order_id + (boarding_order_id, occurred_on) 唯一约束
    with op.batch_alter_table("cost_records", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "boarding_order_id",
                sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
                nullable=True,
            )
        )
        batch_op.create_foreign_key(
            "fk_costs_boarding", "boarding_orders", ["boarding_order_id"], ["id"], ondelete="CASCADE"
        )
        batch_op.create_unique_constraint(
            "uk_costs_boarding_day", ["boarding_order_id", "occurred_on"]
        )


def downgrade() -> None:
    with op.batch_alter_table("cost_records", schema=None) as batch_op:
        batch_op.drop_constraint("uk_costs_boarding_day", type_="unique")
        batch_op.drop_constraint("fk_costs_boarding", type_="foreignkey")
        batch_op.drop_column("boarding_order_id")

    with op.batch_alter_table("boarding_orders", schema=None) as batch_op:
        batch_op.drop_index("idx_boarding_status")
        batch_op.drop_index("idx_boarding_customer")
        batch_op.drop_index("idx_boarding_pet")
    op.drop_table("boarding_orders")
