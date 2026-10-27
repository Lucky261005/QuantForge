"""add missing datasource enum values (Indian providers, synthetic)

The initial schema created the Postgres `datasource` enum with only four values, but
the app also writes NSE_OFFICIAL, KITE_CONNECT, UPSTOX and ANGEL_ONE, and now SYNTHETIC
(seeded demo data). SQLite stores the column as plain VARCHAR with no constraint, so
this is a no-op there.

Revision ID: d3a7b9c2e4f6
Revises: c7d4a2f8e1b5
Create Date: 2026-10-27 06:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d3a7b9c2e4f6"
down_revision: Union[str, None] = "c7d4a2f8e1b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_VALUES = ("NSE_OFFICIAL", "KITE_CONNECT", "UPSTOX", "ANGEL_ONE", "SYNTHETIC")


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    for value in NEW_VALUES:
        op.execute(f"ALTER TYPE datasource ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # Postgres cannot drop a value from an enum type without recreating it; rows may
    # already use these values, so downgrade leaves the type as is.
    pass
