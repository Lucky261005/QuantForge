"""Phase 4 regression tests: metric edge cases that crashed or reported wrong units."""

import json

import numpy as np
import pandas as pd
import pytest

from app.backtesting.engine import BacktestConfig, run_single_asset_backtest
from app.backtesting.metrics import compute_bootstrap_confidence_intervals, compute_performance_metrics

NO_COSTS = {"commission_pct": 0.0, "slippage_pct": 0.0}


def _linear(start: float, end: float, n: int) -> pd.DataFrame:
    close = np.linspace(start, end, n)
    idx = pd.bdate_range("2024-01-01", periods=n)
    return pd.DataFrame({"open": close, "high": close, "low": close, "close": close, "volume": 1.0}, index=idx)


@pytest.mark.parametrize("n", [30, 120])  # below and above the bootstrap's minimum sample
def test_losing_short_with_equity_below_zero_reports_total_loss_instead_of_crashing(n):
    # A short has no margin call in this engine, so a tripling price drives equity below zero.
    df = _linear(100, 300, n)
    result = run_single_asset_backtest(df, pd.Series(-1.0, index=df.index), BacktestConfig(**NO_COSTS))
    assert result.equity_curve.iloc[-1] < 0

    metrics = compute_performance_metrics(result.equity_curve, result.trades)

    # Annualised growth is undefined past a total loss; it is floored at -100%.
    assert metrics.cagr_pct == pytest.approx(-100.0)
    assert metrics.cagr_pct_ci_low == pytest.approx(-100.0)
    assert metrics.total_return_pct < -100.0  # the raw loss itself is still reported in full
    # Every scalar must be a finite real number, or the API cannot serialise the result.
    scalars = {k: v for k, v in vars(metrics).items() if isinstance(v, int | float)}
    json.dumps(scalars, allow_nan=False)


@pytest.mark.parametrize("returns", [[-3.0, 0.01, 0.01, 0.01], [-1.2] + [0.01] * 59])
def test_bootstrap_cagr_interval_is_floored_at_total_loss(returns):
    # A day losing more than 100% (equity crossing below zero) makes compounded growth negative.
    _, _, cagr_low, _ = compute_bootstrap_confidence_intervals(pd.Series(returns), block_size=5)
    assert cagr_low == pytest.approx(-100.0)


def test_profit_factor_with_no_losing_trades_is_a_ratio_not_a_rupee_amount():
    df = _linear(100, 130, 30)
    small = run_single_asset_backtest(
        df, pd.Series(1.0, index=df.index), BacktestConfig(initial_capital=100_000, **NO_COSTS)
    )
    large = run_single_asset_backtest(
        df, pd.Series(1.0, index=df.index), BacktestConfig(initial_capital=10_000_000, **NO_COSTS)
    )
    assert all(t.pnl > 0 for t in small.trades)

    pf_small = compute_performance_metrics(small.equity_curve, small.trades).profit_factor
    pf_large = compute_performance_metrics(large.equity_curve, large.trades).profit_factor
    # A ratio cannot depend on account size; it previously returned gross profit in rupees.
    assert pf_small == pf_large
    # Same cap the module already uses for Omega when there are no losses.
    assert pf_small == pytest.approx(999.0)
