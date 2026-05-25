"""add default_amount to cost_categories

Revision ID: 9b2e1f3a5c10
Revises: 8a1c9d2e4f01
Create Date: 2026-05-25 10:00:00.000000

为什么：服务项目可设默认价（如洗澡 ¥80），录单选完分类自动填金额，省去重复手输。
nullable，因为医疗/零售类无固定价；不破坏现有 cost_records。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b2e1f3a5c10"
down_revision: Union[str, Sequence[str], None] = "2d09493ee593"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("cost_categories", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("default_amount", sa.Numeric(precision=10, scale=2), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("cost_categories", schema=None) as batch_op:
        batch_op.drop_column("default_amount")
