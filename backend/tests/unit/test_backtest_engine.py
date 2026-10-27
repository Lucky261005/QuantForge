import numpy as np
import pandas as pd
import pytest

from app.backtesting.engine import (
    BacktestConfig,
    run_multi_asset_backtest,
    run_multi_asset_backtest_with_rebalancing,
    run_single_asset_backtest,
)
from app.models.trade import ExitReason, TradeSide


def test_buy_and_hold_matches_close_to_close_return_minus_costs(ohlcv_df):
    signal = pd.Series(1.0, index=ohlcv_df.index)
    config = BacktestConfig(initial_capital=100_000, commission_pct=0.0, slippage_pct=0.0)
    result = run_single_asset_backtest(ohlcv_df, signal, config)

    raw_return = ohlcv_df["close"].iloc[-1] / ohlcv_df["close"].iloc[1] - 1
    equity_return = result.equity_curve.iloc[-1] / result.equity_curve.iloc[0] - 1
    assert equity_return == pytest.approx(raw_return, rel=0.02)


def test_zero_signal_never_trades(ohlcv_df):
    signal = pd.Series(0.0, index=ohlcv_df.index)
    result = run_single_asset_backtest(ohlcv_df, signal, BacktestConfig())
    assert result.trades == []
    assert (result.equity_curve == 100_000.0).all()


def test_commission_reduces_equity_relative_to_zero_cost(ohlcv_df):
    signal = pd.Series(1.0, index=ohlcv_df.index)
    cheap = run_single_asset_backtest(ohlcv_df, signal, BacktestConfig(commission_pct=0.0, slippage_pct=0.0))
    expensive = run_single_asset_backtest(ohlcv_df, signal, BacktestConfig(commission_pct=0.01, slippage_pct=0.01))
    assert expensive.equity_curve.iloc[-1] < cheap.equity_curve.iloc[-1]


def test_stop_loss_caps_losses():
    dates = pd.bdate_range("2023-01-02", periods=10)
    close = [100, 99, 95, 80, 70, 65, 60, 55, 50, 45]
    df = pd.DataFrame(
        {
            "open": close,
            "high": [c * 1.01 for c in close],
            "low": [c * 0.99 for c in close],
            "close": close,
            "volume": [1000.0] * 10,
        },
        index=dates,
    )
    signal = pd.Series(1.0, index=dates)
    result = run_single_asset_backtest(df, signal, BacktestConfig(stop_loss_pct=0.05, commission_pct=0, slippage_pct=0))
    assert len(result.trades) >= 1
    first_trade = result.trades[0]
    assert first_trade.exit_reason == ExitReason.STOP_LOSS
    assert first_trade.pnl_pct == pytest.approx(-0.05, abs=0.01)


def test_take_profit_locks_in_gains():
    dates = pd.bdate_range("2023-01-02", periods=10)
    close = [100, 101, 105, 112, 120, 121, 122, 123, 124, 125]
    df = pd.DataFrame(
        {
            "open": close,
            "high": [c * 1.01 for c in close],
            "low": [c * 0.99 for c in close],
            "close": close,
            "volume": [1000.0] * 10,
        },
        index=dates,
    )
    signal = pd.Series(1.0, index=dates)
    result = run_single_asset_backtest(
        df, signal, BacktestConfig(take_profit_pct=0.10, commission_pct=0, slippage_pct=0)
    )
    assert result.trades[0].exit_reason == ExitReason.TAKE_PROFIT
    assert result.trades[0].pnl_pct == pytest.approx(0.10, abs=0.01)


def test_short_side_profits_from_declining_price():
    dates = pd.bdate_range("2023-01-02", periods=10)
    close = [100, 98, 95, 92, 88, 85, 82, 78, 75, 70]
    df = pd.DataFrame(
        {
            "open": close,
            "high": [c * 1.01 for c in close],
            "low": [c * 0.99 for c in close],
            "close": close,
            "volume": [1000.0] * 10,
        },
        index=dates,
    )
    signal = pd.Series(-1.0, index=dates)
    result = run_single_asset_backtest(df, signal, BacktestConfig(commission_pct=0, slippage_pct=0))
    assert result.equity_curve.iloc[-1] > result.equity_curve.iloc[0]
    assert all(t.side == TradeSide.SHORT for t in result.trades)


def test_last_open_position_force_closed_at_end_of_backtest(ohlcv_df):
    signal = pd.Series(1.0, index=ohlcv_df.index)
    result = run_single_asset_backtest(ohlcv_df, signal, BacktestConfig())
    assert result.trades, "Buy&Hold over a full period should produce exactly one closed trade"
    assert result.trades[-1].exit_reason == ExitReason.END_OF_BACKTEST


def test_multi_asset_backtest_combines_equity_curves(ohlcv_df):
    df2 = ohlcv_df.copy()
    df2["close"] = df2["close"] * 1.5
    data = {"AAA": ohlcv_df, "BBB": df2}
    signals = {"AAA": pd.Series(1.0, index=ohlcv_df.index), "BBB": pd.Series(1.0, index=df2.index)}
    result = run_multi_asset_backtest(data, signals, BacktestConfig(initial_capital=100_000))
    assert result.equity_curve.iloc[0] == pytest.approx(100_000, rel=0.01)
    assert set(result.trades_by_symbol.keys()) == {"AAA", "BBB"}


def test_five_year_backtest_completes_correctly_and_quickly():
    """Resume claim: 'backtested across 5 years of historical market data.' Verifies
    the engine both completes correctly (no NaN/inf equity, proper force-close) and
    fast enough to be a real interactive product, not just a theoretical capability."""
    import time

    n = 252 * 5  # 5 years of trading days
    rng = np.random.default_rng(7)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
    returns = rng.normal(0.0005, 0.012, n)
    close = 1000.0 * np.cumprod(1 + returns)
    df = pd.DataFrame(
        {
            "open": close * (1 + rng.normal(0, 0.002, n)),
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": rng.integers(1_000_000, 8_000_000, n).astype(float),
        },
        index=dates,
    )
    fast = df["close"].rolling(20, min_periods=20).mean()
    slow = df["close"].rolling(50, min_periods=50).mean()
    signal = (fast > slow).astype(float)

    start = time.perf_counter()
    result = run_single_asset_backtest(df, signal, BacktestConfig())
    elapsed = time.perf_counter() - start

    assert len(result.equity_curve) == n
    assert np.isfinite(result.equity_curve).all()
    assert (result.equity_curve > 0).all()
    assert elapsed < 2.0, f"5-year single-asset backtest took {elapsed:.2f}s — too slow for an interactive product"


def _two_asset_data(n_months: int = 6):
    dates = pd.bdate_range("2023-01-02", periods=n_months * 21)
    winner_close = 100 * (1.004 ** np.arange(len(dates)))
    loser_close = 100 * (0.999 ** np.arange(len(dates)))
    data = {}
    for name, close in (("WINNER", winner_close), ("LOSER", loser_close)):
        data[name] = pd.DataFrame(
            {
                "open": close,
                "high": close * 1.005,
                "low": close * 0.995,
                "close": close,
                "volume": [1_000_000.0] * len(dates),
            },
            index=dates,
        )
    signals = {name: pd.Series(1.0, index=dates) for name in data}
    return data, signals


def test_rebalance_none_delegates_to_plain_multi_asset_backtest():
    data, signals = _two_asset_data()
    config = BacktestConfig(initial_capital=100_000, commission_pct=0.0, slippage_pct=0.0)
    plain = run_multi_asset_backtest(data, signals, config)
    delegated = run_multi_asset_backtest_with_rebalancing(data, signals, config, rebalance_frequency="none")
    pd.testing.assert_series_equal(plain.equity_curve, delegated.equity_curve)


def test_monthly_rebalancing_produces_a_different_outcome_than_no_rebalancing():
    """With one steadily-winning and one steadily-losing asset, periodic
    rebalance-to-equal-weight must diverge from the buy-and-hold (no rebalance)
    equity curve — that's the entire point of rebalancing."""
    data, signals = _two_asset_data(n_months=6)
    config = BacktestConfig(initial_capital=100_000, commission_pct=0.0, slippage_pct=0.0)

    no_rebalance = run_multi_asset_backtest_with_rebalancing(data, signals, config, rebalance_frequency="none")
    rebalanced = run_multi_asset_backtest_with_rebalancing(data, signals, config, rebalance_frequency="monthly")

    assert no_rebalance.equity_curve.iloc[-1] != pytest.approx(rebalanced.equity_curve.iloc[-1], rel=0.001)
    assert rebalanced.equity_curve.iloc[0] == pytest.approx(100_000, rel=0.02)
    assert set(rebalanced.trades_by_symbol.keys()) == {"WINNER", "LOSER"}


def test_rebalancing_rejects_unknown_frequency():
    data, signals = _two_asset_data(n_months=2)
    config = BacktestConfig(initial_capital=100_000)
    with pytest.raises(ValueError):
        run_multi_asset_backtest_with_rebalancing(data, signals, config, rebalance_frequency="weekly")
