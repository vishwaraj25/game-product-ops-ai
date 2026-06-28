"""add plan product domain

Revision ID: 20260628_0003
Revises: 20260628_0002
Create Date: 2026-06-28 00:03:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260628_0003"
down_revision: Union[str, None] = "20260628_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("investigation_plans", sa.Column("product_domain", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_investigation_plans_product_domain"), "investigation_plans", ["product_domain"])


def downgrade() -> None:
    op.drop_index(op.f("ix_investigation_plans_product_domain"), table_name="investigation_plans")
    op.drop_column("investigation_plans", "product_domain")
