"""add composite index backtests owner_id+status and index strategies is_public

Revision ID: a1c3f9d2b6e4
Revises: e75224f3dee4
Create Date: 2026-07-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1c3f9d2b6e4"
down_revision: Union[str, None] = "e75224f3dee4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_backtests_owner_id_status", "backtests", ["owner_id", "status"])
    op.create_index("ix_strategies_is_public", "strategies", ["is_public"])


def downgrade() -> None:
    op.drop_index("ix_strategies_is_public", table_name="strategies")
    op.drop_index("ix_backtests_owner_id_status", table_name="backtests")
