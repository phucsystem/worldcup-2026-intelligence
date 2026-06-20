"""article intelligence blob

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Holds the full structured intelligence (stakes, group scenarios, per-team
    # notes) backing the home-page widgets. Nullable so existing rows and any
    # caller that omits it round-trip unchanged.
    op.add_column("articles", sa.Column("intelligence", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("articles", "intelligence")
