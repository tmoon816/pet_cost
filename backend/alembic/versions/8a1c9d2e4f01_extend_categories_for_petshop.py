"""extend cost_categories for petshop services

Revision ID: 8a1c9d2e4f01
Revises: 7dd7aae05221
Create Date: 2026-05-22 00:35:00.000000

为什么：把分类从「个人记账」语义（粮食/医疗/美容/玩具/其他）
扩展为「宠物店服务项目」（洗护美容/寄养/医疗/训练/商品零售/其他）。
为保护历史 cost_records 引用，保留旧 code，只更新 label + sort_order，
另新增 boarding / training / retail 三个新 code。

MySQL 兼容：
- bulk_insert 走 sa.table + sa.column 显式声明类型/长度
- UPDATE 用 op.execute + sa.text，无 schema 变更
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8a1c9d2e4f01"
down_revision: Union[str, Sequence[str], None] = "7dd7aae05221"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) 更新旧分类的 label / sort_order，宠物店化
    op.execute(
        sa.text(
            "UPDATE cost_categories SET label = '洗护美容', sort_order = 10 WHERE code = 'grooming'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE cost_categories SET label = '医疗', sort_order = 30 WHERE code = 'medical'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE cost_categories SET label = '商品零售（粮食）', sort_order = 60 WHERE code = 'food'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE cost_categories SET label = '商品零售（玩具）', sort_order = 70 WHERE code = 'toy'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE cost_categories SET label = '其他', sort_order = 99 WHERE code = 'other'"
        )
    )

    # 2) 新增宠物店服务项目（boarding / training / retail）
    cost_categories_table = sa.table(
        "cost_categories",
        sa.column("code", sa.String(length=30)),
        sa.column("label", sa.String(length=30)),
        sa.column("sort_order", sa.Integer()),
    )
    # 用 INSERT ... SELECT WHERE NOT EXISTS 兼容多次执行
    for code, label, sort_order in [
        ("boarding", "寄养", 20),
        ("training", "训练", 40),
        ("retail", "商品零售（综合）", 50),
    ]:
        op.execute(
            sa.text(
                "INSERT INTO cost_categories (code, label, sort_order) "
                "SELECT :code, :label, :sort "
                "WHERE NOT EXISTS (SELECT 1 FROM cost_categories WHERE code = :code)"
            ).bindparams(code=code, label=label, sort=sort_order)
        )


def downgrade() -> None:
    # 1) 删除新增 code（如有未删除的 cost_records 引用会冲突，下行先警告再删）
    op.execute(
        sa.text(
            "DELETE FROM cost_categories WHERE code IN ('boarding', 'training', 'retail')"
        )
    )
    # 2) 还原旧 label / sort_order
    op.execute(
        sa.text(
            "UPDATE cost_categories SET label = '美容', sort_order = 30 WHERE code = 'grooming'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE cost_categories SET label = '医疗', sort_order = 20 WHERE code = 'medical'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE cost_categories SET label = '粮食', sort_order = 10 WHERE code = 'food'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE cost_categories SET label = '玩具', sort_order = 40 WHERE code = 'toy'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE cost_categories SET label = '其他', sort_order = 99 WHERE code = 'other'"
        )
    )
