"""add risk_free_rate_annual to backtests and bootstrap CI columns to backtest_results

Revision ID: f2b8e6a1c9d3
Revises: a1c3f9d2b6e4
Create Date: 2026-07-25 11:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f2b8e6a1c9d3"
down_revision: Union[str, None] = "a1c3f9d2b6e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("backtests", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("risk_free_rate_annual", sa.Float(), nullable=False, server_default="0.0")
        )

    with op.batch_alter_table("backtest_results", schema=None) as batch_op:
        batch_op.add_column(sa.Column("sharpe_ratio_ci_low", sa.Float(), nullable=False, server_default="0.0"))
        batch_op.add_column(sa.Column("sharpe_ratio_ci_high", sa.Float(), nullable=False, server_default="0.0"))
        batch_op.add_column(sa.Column("cagr_pct_ci_low", sa.Float(), nullable=False, server_default="0.0"))
        batch_op.add_column(sa.Column("cagr_pct_ci_high", sa.Float(), nullable=False, server_default="0.0"))


def downgrade() -> None:
    with op.batch_alter_table("backtest_results", schema=None) as batch_op:
        batch_op.drop_column("cagr_pct_ci_high")
        batch_op.drop_column("cagr_pct_ci_low")
        batch_op.drop_column("sharpe_ratio_ci_high")
        batch_op.drop_column("sharpe_ratio_ci_low")

    with op.batch_alter_table("backtests", schema=None) as batch_op:
        batch_op.drop_column("risk_free_rate_annual")
