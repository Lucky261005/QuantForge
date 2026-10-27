import numpy as np
import pandas as pd
import pytest

from app.backtesting.engine import BacktestConfig, run_single_asset_backtest
from app.backtesting.metrics import compute_bootstrap_confidence_intervals, compute_performance_metrics


def test_metrics_on_flat_equity_curve_are_zeroed_out():
    dates = pd.bdate_range("2023-01-02", periods=100)
    equity = pd.Series(100_000.0, index=dates)
    metrics = compute_performance_metrics(equity, trades=[])
    assert metrics.total_return_pct == pytest.approx(0.0)
    assert metrics.max_drawdown_pct == pytest.approx(0.0)
    assert metrics.num_trades == 0
    assert metrics.win_rate_pct == 0.0


def test_metrics_on_steadily_rising_equity_has_positive_sharpe():
    dates = pd.bdate_range("2023-01-02", periods=252)
    equity = pd.Series(100_000 * (1.0005 ** np.arange(252)), index=dates)
    metrics = compute_performance_metrics(equity, trades=[])
    assert metrics.total_return_pct > 0
    assert metrics.sharpe_ratio > 0
    assert metrics.max_drawdown_pct == pytest.approx(0.0, abs=0.01)


def test_max_drawdown_detected_correctly():
    dates = pd.bdate_range("2023-01-02", periods=10)
    equity = pd.Series([100, 110, 120, 90, 95, 100, 130, 140, 135, 145], index=dates, dtype=float) * 1000
    metrics = compute_performance_metrics(equity, trades=[])
    expected_dd = (90 - 120) / 120 * 100
    assert metrics.max_drawdown_pct == pytest.approx(expected_dd, rel=0.01)


def test_win_rate_and_profit_factor_from_trades(ohlcv_df):
    signal = pd.Series(1.0, index=ohlcv_df.index)
    result = run_single_asset_backtest(ohlcv_df, signal, BacktestConfig(stop_loss_pct=0.03, take_profit_pct=0.05))
    metrics = compute_performance_metrics(result.equity_curve, result.trades)
    assert 0 <= metrics.win_rate_pct <= 100
    assert metrics.profit_factor >= 0
    assert metrics.num_trades == len(result.trades)


def test_alpha_beta_computed_against_benchmark(ohlcv_df):
    signal = pd.Series(1.0, index=ohlcv_df.index)
    result = run_single_asset_backtest(ohlcv_df, signal, BacktestConfig(commission_pct=0, slippage_pct=0))
    benchmark_returns = ohlcv_df["close"].pct_change().fillna(0.0)
    metrics = compute_performance_metrics(result.equity_curve, result.trades, benchmark_returns=benchmark_returns)
    # Strategy IS the benchmark (buy & hold on the same series), so beta should be ~1, alpha ~0.
    assert metrics.beta == pytest.approx(1.0, abs=0.05)
    assert metrics.alpha == pytest.approx(0.0, abs=0.05)


def test_json_payloads_are_serializable(ohlcv_df):
    import json

    signal = pd.Series(1.0, index=ohlcv_df.index)
    result = run_single_asset_backtest(ohlcv_df, signal, BacktestConfig())
    metrics = compute_performance_metrics(result.equity_curve, result.trades)
    json.dumps(metrics.equity_curve)
    json.dumps(metrics.drawdown_curve)
    json.dumps(metrics.monthly_returns)
    json.dumps(metrics.daily_returns)
    assert metrics.omega_ratio < float("inf")


def test_risk_free_rate_lowers_sharpe_and_sortino(ohlcv_df):
    signal = pd.Series(1.0, index=ohlcv_df.index)
    result = run_single_asset_backtest(ohlcv_df, signal, BacktestConfig(commission_pct=0, slippage_pct=0))
    zero_rf = compute_performance_metrics(result.equity_curve, result.trades, risk_free_rate_annual=0.0)
    with_rf = compute_performance_metrics(result.equity_curve, result.trades, risk_free_rate_annual=0.07)
    assert with_rf.sharpe_ratio < zero_rf.sharpe_ratio
    assert with_rf.sortino_ratio < zero_rf.sortino_ratio


def test_bootstrap_confidence_interval_brackets_the_point_estimate(ohlcv_df):
    signal = pd.Series(1.0, index=ohlcv_df.index)
    result = run_single_asset_backtest(ohlcv_df, signal, BacktestConfig(commission_pct=0, slippage_pct=0))
    # N equity points give N-1 returns (no padded 0% first day), matching the metrics.
    daily_returns = result.equity_curve.pct_change().iloc[1:]
    metrics = compute_performance_metrics(result.equity_curve, result.trades)

    assert metrics.sharpe_ratio_ci_low <= metrics.sharpe_ratio_ci_high
    assert metrics.cagr_pct_ci_low <= metrics.cagr_pct_ci_high

    # Sanity check against calling the bootstrap function directly with the same inputs.
    direct = compute_bootstrap_confidence_intervals(daily_returns)
    assert direct == (
        metrics.sharpe_ratio_ci_low,
        metrics.sharpe_ratio_ci_high,
        metrics.cagr_pct_ci_low,
        metrics.cagr_pct_ci_high,
    )


def test_bootstrap_is_deterministic_given_the_same_seed(ohlcv_df):
    daily_returns = ohlcv_df["close"].pct_change().fillna(0.0)
    first = compute_bootstrap_confidence_intervals(daily_returns, seed=42)
    second = compute_bootstrap_confidence_intervals(daily_returns, seed=42)
    assert first == second


def test_bootstrap_handles_too_little_data_without_crashing():
    tiny_returns = pd.Series([0.01, -0.005, 0.002])
    low, high, cagr_low, cagr_high = compute_bootstrap_confidence_intervals(tiny_returns, block_size=20)
    assert low == high  # degenerate interval when there's not enough data to resample blocks
    assert cagr_low == cagr_high


def test_five_year_metrics_computation_completes_quickly():
    """The bootstrap adds real computation on top of the already-vectorized engine —
    verifies it doesn't turn a 5-year backtest into a slow one."""
    import time

    n = 252 * 5
    rng = np.random.default_rng(11)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
    equity = pd.Series(100_000.0 * np.cumprod(1 + rng.normal(0.0004, 0.01, n)), index=dates)

    start = time.perf_counter()
    compute_performance_metrics(equity, trades=[])
    elapsed = time.perf_counter() - start

    assert elapsed < 3.0, f"5-year metrics computation (incl. bootstrap) took {elapsed:.2f}s — too slow"
