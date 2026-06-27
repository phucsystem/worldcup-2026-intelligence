"""match forecast_kind column — 'group' | 'ko' | null

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("matches", sa.Column("forecast_kind", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "forecast_kind")
