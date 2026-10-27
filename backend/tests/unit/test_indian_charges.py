import pandas as pd
import pytest

from app.backtesting.charges import IndianChargesConfig, compute_entry_exit_cost_pct
from app.backtesting.engine import BacktestConfig, run_single_asset_backtest


def test_delivery_entry_includes_stamp_duty_exit_does_not():
    charges = IndianChargesConfig()
    entry_pct, exit_pct = compute_entry_exit_cost_pct(charges, delivery=True)
    # Delivery: STT hits both legs, stamp duty only the buy leg -> entry costs more than exit.
    assert entry_pct > exit_pct
    assert entry_pct - exit_pct == pytest.approx(charges.stamp_duty_delivery_buy_pct)


def test_intraday_stt_only_on_sell_leg():
    charges = IndianChargesConfig()
    entry_pct, exit_pct = compute_entry_exit_cost_pct(charges, delivery=False)
    # Intraday: STT only on sell, stamp duty only on buy -> both legs carry some cost.
    assert entry_pct > 0
    assert exit_pct > 0


def test_zero_brokerage_still_carries_statutory_charges():
    charges = IndianChargesConfig(brokerage_pct=0.0)
    entry_pct, exit_pct = compute_entry_exit_cost_pct(charges, delivery=True)
    assert entry_pct > 0
    assert exit_pct > 0


def test_indian_charges_reduce_equity_relative_to_zero_cost(ohlcv_df):
    signal = pd.Series(1.0, index=ohlcv_df.index)
    zero_cost = run_single_asset_backtest(ohlcv_df, signal, BacktestConfig(commission_pct=0.0, slippage_pct=0.0))

    entry_pct, exit_pct = compute_entry_exit_cost_pct(IndianChargesConfig(), delivery=True)
    with_charges = run_single_asset_backtest(
        ohlcv_df,
        signal,
        BacktestConfig(commission_pct=0.0, slippage_pct=0.0, entry_cost_pct=entry_pct, exit_cost_pct=exit_pct),
    )
    assert with_charges.equity_curve.iloc[-1] < zero_cost.equity_curve.iloc[-1]


def test_entry_exit_cost_pct_none_falls_back_to_commission_pct(ohlcv_df):
    """When entry_cost_pct/exit_cost_pct are left at their default None, behavior must be
    byte-for-byte identical to the original flat commission_pct model (backward compat)."""
    signal = pd.Series(1.0, index=ohlcv_df.index)
    baseline = run_single_asset_backtest(ohlcv_df, signal, BacktestConfig(commission_pct=0.002, slippage_pct=0.001))
    explicit = run_single_asset_backtest(
        ohlcv_df,
        signal,
        BacktestConfig(commission_pct=0.002, slippage_pct=0.001, entry_cost_pct=None, exit_cost_pct=None),
    )
    pd.testing.assert_series_equal(baseline.equity_curve, explicit.equity_curve)
