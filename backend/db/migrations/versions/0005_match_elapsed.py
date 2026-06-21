"""match live elapsed minute

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Live match minute (fixture.status.elapsed). Nullable so finished/upcoming
    # rows and any caller that omits it round-trip unchanged.
    op.add_column("matches", sa.Column("elapsed", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "elapsed")
