"""Hand-computed checks for the execution and metric corrections: gap fills, short-side
charge legs, return-period count, downside deviation, Jensen's alpha, risk-free-aware
bootstrap, and multi-asset equity before a symbol's first bar."""

import numpy as np
import pandas as pd
import pytest

from app.backtesting.engine import (
    BacktestConfig,
    run_multi_asset_backtest,
    run_multi_asset_backtest_with_rebalancing,
    run_single_asset_backtest,
)
from app.backtesting.metrics import (
    TRADING_DAYS_PER_YEAR,
    compute_bootstrap_confidence_intervals,
    compute_performance_metrics,
)
from app.models.trade import ExitReason, TradeSide


def _bars(rows: list[tuple[float, float, float, float]], start: str = "2024-01-01") -> pd.DataFrame:
    """rows of (open, high, low, close)."""
    idx = pd.bdate_range(start, periods=len(rows))
    o, h, lo, c = zip(*rows, strict=True)
    return pd.DataFrame({"open": o, "high": h, "low": lo, "close": c, "volume": 1000.0}, index=idx)


NO_COSTS = {"commission_pct": 0.0, "slippage_pct": 0.0}


def test_long_stop_gapped_through_fills_at_the_open_not_the_stop():
    # Enter at day-1 close 100 (signal on day 0). Stop 5% = 95. Day 2 opens at 90.
    df = _bars([(100, 100, 100, 100), (100, 101, 99, 100), (90, 91, 88, 89), (89, 90, 88, 89)])
    signal = pd.Series([1, 1, 1, 1], index=df.index, dtype=float)
    trade = run_single_asset_backtest(df, signal, BacktestConfig(stop_loss_pct=0.05, **NO_COSTS)).trades[0]
    assert trade.exit_reason == ExitReason.STOP_LOSS
    assert trade.exit_price == pytest.approx(90.0)  # not the unreachable 95
    assert trade.pnl_pct == pytest.approx(-0.10)


def test_long_stop_touched_intraday_still_fills_at_the_stop():
    df = _bars([(100, 100, 100, 100), (100, 101, 99, 100), (99, 99, 94, 96), (96, 97, 95, 96)])
    signal = pd.Series([1, 1, 1, 1], index=df.index, dtype=float)
    trade = run_single_asset_backtest(df, signal, BacktestConfig(stop_loss_pct=0.05, **NO_COSTS)).trades[0]
    assert trade.exit_price == pytest.approx(95.0)


def test_long_target_gapped_through_fills_at_the_better_open():
    df = _bars([(100, 100, 100, 100), (100, 101, 99, 100), (115, 116, 114, 115), (115, 116, 114, 115)])
    signal = pd.Series([1, 1, 1, 1], index=df.index, dtype=float)
    trade = run_single_asset_backtest(df, signal, BacktestConfig(take_profit_pct=0.10, **NO_COSTS)).trades[0]
    assert trade.exit_reason == ExitReason.TAKE_PROFIT
    assert trade.exit_price == pytest.approx(115.0)


def test_short_stop_gapped_through_fills_at_the_open():
    df = _bars([(100, 100, 100, 100), (100, 101, 99, 100), (110, 112, 109, 111), (111, 112, 110, 111)])
    signal = pd.Series([-1, -1, -1, -1], index=df.index, dtype=float)
    trade = run_single_asset_backtest(df, signal, BacktestConfig(stop_loss_pct=0.05, **NO_COSTS)).trades[0]
    assert trade.side == TradeSide.SHORT
    assert trade.exit_price == pytest.approx(110.0)  # worse than the 105 stop


def test_short_trade_pays_sell_leg_cost_to_open_and_buy_leg_cost_to_close():
    # Buy leg costs 1%, sell leg 2%. A short opens with a sale and closes with a purchase.
    df = _bars([(100, 100, 100, 100), (100, 100, 100, 100), (80, 80, 80, 80)])
    signal = pd.Series([-1, -1, -1], index=df.index, dtype=float)
    config = BacktestConfig(
        initial_capital=10_000, commission_pct=0.0, slippage_pct=0.0, entry_cost_pct=0.01, exit_cost_pct=0.02
    )
    trade = run_single_asset_backtest(df, signal, config).trades[0]

    notional = 10_000 * (1 - 0.02)  # sell-leg cost on entry
    qty = notional / 100
    expected_pnl = qty * (100 - 80) - qty * 80 * 0.01  # buy-leg cost on exit
    assert trade.quantity == pytest.approx(qty)
    assert trade.pnl == pytest.approx(expected_pnl)


def test_cagr_counts_return_periods_not_equity_points():
    # 253 equity points = 252 daily returns = exactly one trading year at 0.1%/day.
    g = 0.001
    equity = pd.Series(100_000 * (1 + g) ** np.arange(253), index=pd.bdate_range("2024-01-01", periods=253))
    metrics = compute_performance_metrics(equity, [])
    assert metrics.cagr_pct == pytest.approx(((1 + g) ** 252 - 1) * 100)


def test_sortino_uses_downside_deviation_over_all_periods():
    returns = np.array([0.02, -0.01, 0.03, -0.02, 0.01])
    equity = pd.Series(100 * np.cumprod(np.r_[1.0, 1 + returns]), index=pd.bdate_range("2024-01-01", periods=6))
    metrics = compute_performance_metrics(equity, [])

    downside_deviation = np.sqrt(np.mean(np.minimum(returns, 0.0) ** 2))  # over all 5 periods
    expected = returns.mean() / downside_deviation * np.sqrt(TRADING_DAYS_PER_YEAR)
    assert metrics.sortino_ratio == pytest.approx(expected)


def test_alpha_is_jensens_alpha_net_of_the_risk_free_rate():
    # Strategy = risk-free + 0.5 x benchmark excess, exactly: beta 0.5 and Jensen's alpha 0.
    rf_annual = 0.06
    rf_daily = rf_annual / TRADING_DAYS_PER_YEAR
    rng = np.random.default_rng(7)
    idx = pd.bdate_range("2024-01-01", periods=301)
    bench = pd.Series(rng.normal(0.0008, 0.01, 300), index=idx[1:])
    strat = rf_daily + 0.5 * (bench - rf_daily)
    equity = pd.Series(100_000 * np.cumprod(np.r_[1.0, 1 + strat.to_numpy()]), index=idx)

    metrics = compute_performance_metrics(equity, [], benchmark_returns=bench, risk_free_rate_annual=rf_annual)
    assert metrics.beta == pytest.approx(0.5, abs=1e-9)
    assert metrics.alpha == pytest.approx(0.0, abs=1e-9)


def test_bootstrap_sharpe_interval_is_net_of_the_risk_free_rate():
    rng = np.random.default_rng(3)
    returns = pd.Series(rng.normal(0.0006, 0.01, 500))
    rf_daily = 0.07 / TRADING_DAYS_PER_YEAR
    lo0, hi0, *_ = compute_bootstrap_confidence_intervals(returns)
    lo_rf, hi_rf, *_ = compute_bootstrap_confidence_intervals(returns, rf_daily=rf_daily)
    assert lo_rf < lo0 and hi_rf < hi0


def test_multi_asset_equity_before_a_symbols_first_bar_is_its_idle_capital():
    # Regression guard: before LATE's first bar its share of capital counts at face value.
    early = _bars([(100, 100, 100, 100)] * 5, start="2024-01-01")
    late = _bars([(50, 50, 50, 50)] * 3, start="2024-01-03")
    signals = {"EARLY": pd.Series(0.0, index=early.index), "LATE": pd.Series(1.0, index=late.index)}
    result = run_multi_asset_backtest(
        {"EARLY": early, "LATE": late}, signals, BacktestConfig(initial_capital=100_000, commission_pct=0.01)
    )
    assert result.equity_curve.iloc[:2].to_numpy() == pytest.approx([100_000, 100_000])


def test_rebalanced_equity_keeps_capital_of_symbols_with_no_bars_that_period():
    # LATE has no bars in January or February. With monthly rebalancing and no trades,
    # total equity must stay at 100,000 every day; the bug dropped LATE's idle half.
    early = _bars([(100, 100, 100, 100)] * 60, start="2024-01-01")
    late = _bars([(50, 50, 50, 50)] * 15, start="2024-03-01")
    signals = {"EARLY": pd.Series(0.0, index=early.index), "LATE": pd.Series(0.0, index=late.index)}
    result = run_multi_asset_backtest_with_rebalancing(
        {"EARLY": early, "LATE": late},
        signals,
        BacktestConfig(initial_capital=100_000),
        rebalance_frequency="monthly",
    )
    assert result.equity_curve.min() == pytest.approx(100_000)
    assert result.equity_curve.max() == pytest.approx(100_000)
