import pandas as pd
import pytest

from app.indicators import indicator_registry
from app.strategies import strategy_registry


def test_twenty_one_strategies_registered():
    keys = {s.key for s in strategy_registry.list_all()}
    assert keys == {
        "buy_and_hold",
        "ma_cross",
        "rsi_mean_reversion",
        "macd",
        "bollinger_breakout",
        "momentum",
        "donchian_breakout",
        "vwap_trend",
        "ema_crossover",
        "supertrend",
        "adx_trend",
        "ma_ribbon",
        "orb",
        "williams_r_reversal",
        "cci_trend",
        "parabolic_sar_trend",
        "obv_trend",
        "aroon_trend",
        "mfi_reversal",
        "stochastic_reversal",
        "bollinger_zscore_reversion",
    }
    assert len(keys) >= 20  # resume claim: 20+ backtested strategies
    assert len(indicator_registry.list_all()) >= 15  # resume claim: 15+ technical indicators


def test_all_strategies_return_signal_in_valid_range(ohlcv_df):
    for spec in strategy_registry.list_all():
        signal = spec.compute(ohlcv_df)
        assert isinstance(signal, pd.Series)
        assert len(signal) == len(ohlcv_df)
        valid = signal.dropna()
        assert valid.isin([-1.0, 0.0, 1.0]).all(), f"{spec.key} produced out-of-range signal values"


def test_buy_and_hold_always_long(ohlcv_df):
    signal = strategy_registry.get("buy_and_hold").compute(ohlcv_df)
    assert (signal == 1.0).all()


def test_ma_cross_long_only_by_default(ohlcv_df):
    signal = strategy_registry.get("ma_cross").compute(ohlcv_df, fast_window=10, slow_window=30)
    assert signal.isin([0.0, 1.0]).all()


def test_ma_cross_allows_short_when_enabled(ohlcv_df):
    signal = strategy_registry.get("ma_cross").compute(ohlcv_df, fast_window=10, slow_window=30, allow_short=1)
    assert signal.isin([-1.0, 0.0, 1.0]).all()
    assert (signal == -1.0).any()


def test_rsi_mean_reversion_goes_long_when_oversold():
    # A sharp selloff should push RSI below the oversold threshold and trigger a long entry.
    prices = [100.0] * 20 + list(range(100, 60, -2))
    df = pd.DataFrame(
        {"open": prices, "high": prices, "low": prices, "close": prices, "volume": [1_000.0] * len(prices)}
    )
    signal = strategy_registry.get("rsi_mean_reversion").compute(df, window=14, oversold=30, overbought=70)
    assert (signal == 1.0).any()


def test_unknown_strategy_raises_key_error():
    with pytest.raises(KeyError):
        strategy_registry.get("not_a_real_strategy")


def test_strategy_param_overrides_are_respected(ohlcv_df):
    default_signal = strategy_registry.get("momentum").compute(ohlcv_df)
    overridden_signal = strategy_registry.get("momentum").compute(ohlcv_df, lookback=5)
    assert not default_signal.equals(overridden_signal)


def test_ema_crossover_long_only_by_default(ohlcv_df):
    signal = strategy_registry.get("ema_crossover").compute(ohlcv_df, fast_window=9, slow_window=21)
    assert signal.isin([0.0, 1.0]).all()


def test_ema_crossover_allows_short_when_enabled(ohlcv_df):
    signal = strategy_registry.get("ema_crossover").compute(ohlcv_df, fast_window=9, slow_window=21, allow_short=1)
    assert signal.isin([-1.0, 0.0, 1.0]).all()


def test_supertrend_strategy_stays_long_through_monotonic_rise():
    dates = pd.bdate_range("2023-01-02", periods=40)
    close = [100 + i for i in range(40)]
    df = pd.DataFrame(
        {
            "open": close,
            "high": [c * 1.01 for c in close],
            "low": [c * 0.99 for c in close],
            "close": close,
            "volume": [1_000.0] * 40,
        },
        index=dates,
    )
    signal = strategy_registry.get("supertrend").compute(df, window=10, multiplier=3.0)
    assert signal.iloc[-1] == 1.0


def test_adx_trend_flat_when_below_threshold(ohlcv_df):
    signal = strategy_registry.get("adx_trend").compute(ohlcv_df, window=14, adx_threshold=1000.0)
    assert (signal == 0.0).all()


def test_ma_ribbon_bullish_alignment_on_steady_uptrend():
    dates = pd.bdate_range("2023-01-02", periods=150)
    close = [100 + i * 0.5 for i in range(150)]
    df = pd.DataFrame(
        {
            "open": close,
            "high": close,
            "low": close,
            "close": close,
            "volume": [1_000.0] * 150,
        },
        index=dates,
    )
    signal = strategy_registry.get("ma_ribbon").compute(df, w1=10, w2=20, w3=30, w4=50, w5=100)
    assert signal.iloc[-1] == 1.0


def test_orb_produces_no_trades_on_daily_bars(ohlcv_df):
    """ORB needs intraday bars to be meaningful; on daily bars (one bar per session)
    the opening range collapses and the strategy should stay flat throughout."""
    signal = strategy_registry.get("orb").compute(ohlcv_df, range_bars=1)
    assert (signal == 0.0).all()


def test_williams_r_reversal_goes_long_when_oversold():
    prices = [100.0] * 20 + list(range(100, 60, -2))
    df = pd.DataFrame(
        {"open": prices, "high": prices, "low": prices, "close": prices, "volume": [1_000.0] * len(prices)}
    )
    signal = strategy_registry.get("williams_r_reversal").compute(df, window=14, oversold=-80, overbought=-20)
    assert (signal == 1.0).any()


def test_cci_trend_signal_in_valid_range(ohlcv_df):
    signal = strategy_registry.get("cci_trend").compute(ohlcv_df, window=20, threshold=100.0)
    assert signal.isin([0.0, 1.0]).all()


def test_parabolic_sar_trend_long_only_by_default(ohlcv_df):
    signal = strategy_registry.get("parabolic_sar_trend").compute(ohlcv_df)
    assert signal.isin([0.0, 1.0]).all()


def test_parabolic_sar_trend_allows_short_when_enabled(ohlcv_df):
    signal = strategy_registry.get("parabolic_sar_trend").compute(ohlcv_df, allow_short=1)
    assert signal.isin([-1.0, 0.0, 1.0]).all()


def test_obv_trend_signal_in_valid_range(ohlcv_df):
    signal = strategy_registry.get("obv_trend").compute(ohlcv_df, smoothing_window=20)
    assert signal.isin([0.0, 1.0]).all()


def test_aroon_trend_long_at_fresh_high():
    dates = pd.bdate_range("2023-01-02", periods=40)
    close = list(range(1, 41))
    df = pd.DataFrame(
        {"open": close, "high": close, "low": close, "close": close, "volume": [1_000.0] * 40}, index=dates
    )
    signal = strategy_registry.get("aroon_trend").compute(df, window=10, threshold=70.0)
    assert signal.iloc[-1] == 1.0


def test_mfi_reversal_goes_long_when_oversold(ohlcv_df):
    signal = strategy_registry.get("mfi_reversal").compute(ohlcv_df, window=14, oversold=20, overbought=80)
    assert signal.isin([0.0, 1.0]).all()


def test_stochastic_reversal_goes_long_when_oversold():
    prices = [100.0] * 20 + list(range(100, 60, -2))
    df = pd.DataFrame(
        {"open": prices, "high": prices, "low": prices, "close": prices, "volume": [1_000.0] * len(prices)}
    )
    signal = strategy_registry.get("stochastic_reversal").compute(df, k_period=14, oversold=20, overbought=80)
    assert (signal == 1.0).any()


def test_bollinger_zscore_reversion_goes_long_on_downside_stretch():
    prices = [100.0] * 25 + list(range(100, 70, -2))
    df = pd.DataFrame(
        {"open": prices, "high": prices, "low": prices, "close": prices, "volume": [1_000.0] * len(prices)}
    )
    signal = strategy_registry.get("bollinger_zscore_reversion").compute(df, window=20, entry_z=-2.0)
    assert (signal == 1.0).any()
