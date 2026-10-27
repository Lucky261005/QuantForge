"""add rebalance_frequency to backtests

Revision ID: c7d4a2f8e1b5
Revises: f2b8e6a1c9d3
Create Date: 2026-07-25 11:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c7d4a2f8e1b5"
down_revision: Union[str, None] = "f2b8e6a1c9d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("backtests", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("rebalance_frequency", sa.String(length=20), nullable=False, server_default="none")
        )


def downgrade() -> None:
    with op.batch_alter_table("backtests", schema=None) as batch_op:
        batch_op.drop_column("rebalance_frequency")
