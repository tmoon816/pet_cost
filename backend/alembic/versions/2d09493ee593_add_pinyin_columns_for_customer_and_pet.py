"""add pinyin columns for customer and pet

Revision ID: 2d09493ee593
Revises: 8a1c9d2e4f01
Create Date: 2026-05-24 00:44:23.795960

为什么：让搜索支持中文名拼音首字母 / 全拼输入。给 customers 和 pets 各加
name_pinyin（全拼，无分隔）和 name_initials（首字母）两列，并对历史数据回填。

MySQL 兼容：
- 新列默认空串而非 NULL，避免 NULL 拼接和空值排序歧义
- 回填用 pypinyin 在 Python 侧计算后 UPDATE，不依赖 DB 端函数
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d09493ee593'
down_revision: Union[str, Sequence[str], None] = '8a1c9d2e4f01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _backfill(connection, table: str) -> None:
    from app.core.pinyin import to_initials, to_pinyin

    rows = connection.execute(sa.text(f"SELECT id, name FROM {table}")).fetchall()
    for row in rows:
        connection.execute(
            sa.text(
                f"UPDATE {table} SET name_pinyin = :py, name_initials = :ini WHERE id = :id"
            ).bindparams(py=to_pinyin(row.name), ini=to_initials(row.name), id=row.id)
        )


def upgrade() -> None:
    # 1) 加列（NOT NULL + server_default '' 让历史行先有空串占位）
    op.add_column(
        "customers",
        sa.Column("name_pinyin", sa.String(length=255), nullable=False, server_default=""),
    )
    op.add_column(
        "customers",
        sa.Column("name_initials", sa.String(length=50), nullable=False, server_default=""),
    )
    op.add_column(
        "pets",
        sa.Column("name_pinyin", sa.String(length=255), nullable=False, server_default=""),
    )
    op.add_column(
        "pets",
        sa.Column("name_initials", sa.String(length=50), nullable=False, server_default=""),
    )

    # 2) 回填历史数据
    bind = op.get_bind()
    _backfill(bind, "customers")
    _backfill(bind, "pets")

    # 3) 加索引
    op.create_index("idx_customers_name_pinyin", "customers", ["name_pinyin"])
    op.create_index("idx_customers_name_initials", "customers", ["name_initials"])
    op.create_index("idx_pets_name_pinyin", "pets", ["name_pinyin"])
    op.create_index("idx_pets_name_initials", "pets", ["name_initials"])


def downgrade() -> None:
    op.drop_index("idx_pets_name_initials", table_name="pets")
    op.drop_index("idx_pets_name_pinyin", table_name="pets")
    op.drop_index("idx_customers_name_initials", table_name="customers")
    op.drop_index("idx_customers_name_pinyin", table_name="customers")
    op.drop_column("pets", "name_initials")
    op.drop_column("pets", "name_pinyin")
    op.drop_column("customers", "name_initials")
    op.drop_column("customers", "name_pinyin")
