import pandas as pd
import pytest

from app.indicators import indicator_registry


def test_all_indicators_are_registered():
    keys = {spec.key for spec in indicator_registry.list_all()}
    assert keys == {
        "sma",
        "ema",
        "macd",
        "adx",
        "rsi",
        "stochastic",
        "roc",
        "bollinger_bands",
        "atr",
        "vwap",
        "supertrend",
        "williams_r",
        "cci",
        "aroon",
        "parabolic_sar",
        "obv",
        "mfi",
    }


def test_sma_matches_pandas_rolling_mean(ohlcv_df):
    result = indicator_registry.get("sma").compute(ohlcv_df, window=20)
    expected = ohlcv_df["close"].rolling(20).mean()
    pd.testing.assert_series_equal(result["sma"], expected, check_names=False)


def test_ema_converges_to_close_for_window_one(ohlcv_df):
    result = indicator_registry.get("ema").compute(ohlcv_df, window=1)
    pd.testing.assert_series_equal(result["ema"], ohlcv_df["close"], check_names=False, check_exact=False)


def test_rsi_bounded_between_0_and_100(ohlcv_df):
    result = indicator_registry.get("rsi").compute(ohlcv_df, window=14)
    valid = result["rsi"].dropna()
    assert (valid >= 0).all() and (valid <= 100).all()


def test_rsi_is_100_for_monotonically_rising_prices():
    df = pd.DataFrame(
        {
            "open": range(1, 31),
            "high": range(1, 31),
            "low": range(1, 31),
            "close": range(1, 31),
            "volume": [1_000] * 30,
        },
        dtype=float,
    )
    result = indicator_registry.get("rsi").compute(df, window=14)
    assert result["rsi"].iloc[-1] == pytest.approx(100.0)


def test_macd_histogram_equals_macd_minus_signal(ohlcv_df):
    result = indicator_registry.get("macd").compute(ohlcv_df, fast_period=12, slow_period=26, signal_period=9)
    pd.testing.assert_series_equal(result["macd_hist"], result["macd"] - result["macd_signal"], check_names=False)


def test_bollinger_bands_ordering(ohlcv_df):
    result = indicator_registry.get("bollinger_bands").compute(ohlcv_df, window=20, num_std=2.0)
    valid = result.dropna()
    assert (valid["bb_upper"] >= valid["bb_middle"]).all()
    assert (valid["bb_middle"] >= valid["bb_lower"]).all()


def test_atr_is_non_negative(ohlcv_df):
    result = indicator_registry.get("atr").compute(ohlcv_df, window=14)
    assert (result["atr"].dropna() >= 0).all()


def test_stochastic_bounded_between_0_and_100(ohlcv_df):
    result = indicator_registry.get("stochastic").compute(ohlcv_df, k_period=14, d_period=3)
    valid_k = result["stoch_k"].dropna()
    assert (valid_k >= -0.01).all() and (valid_k <= 100.01).all()


def test_adx_non_negative(ohlcv_df):
    result = indicator_registry.get("adx").compute(ohlcv_df, window=14)
    assert (result["adx"].dropna() >= 0).all()


def test_roc_zero_when_flat_prices():
    df = pd.DataFrame(
        {"open": [100.0] * 20, "high": [100.0] * 20, "low": [100.0] * 20, "close": [100.0] * 20, "volume": [1.0] * 20}
    )
    result = indicator_registry.get("roc").compute(df, window=12)
    assert result["roc"].dropna().eq(0).all()


def test_vwap_between_low_and_high_bounds(ohlcv_df):
    result = indicator_registry.get("vwap").compute(ohlcv_df)
    assert (result["vwap"] >= ohlcv_df["low"].cummin() * 0.9).all()
    assert (result["vwap"] <= ohlcv_df["high"].cummax() * 1.1).all()


def test_supertrend_direction_is_plus_or_minus_one(ohlcv_df):
    result = indicator_registry.get("supertrend").compute(ohlcv_df, window=10, multiplier=3.0)
    valid = result["supertrend_direction"].dropna()
    assert set(valid.unique()) <= {1.0, -1.0}


def test_supertrend_locks_onto_uptrend_and_never_flips_back():
    """Direction starts in an arbitrary initial state (standard SuperTrend behavior) but
    for a monotonically rising series, once it flips to uptrend it must stay there —
    the ratcheting lower band never gets breached by a series that only goes up."""
    dates = pd.bdate_range("2023-01-02", periods=40)
    close = [100 + i for i in range(40)]  # steady uptrend
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
    result = indicator_registry.get("supertrend").compute(df, window=10, multiplier=3.0)
    direction = result["supertrend_direction"].dropna()
    assert direction.iloc[-1] == 1.0
    flips_to_uptrend = direction[(direction == 1.0) & (direction.shift(1) == -1.0)]
    assert len(flips_to_uptrend) <= 1, "should flip to uptrend at most once and never flip back"

    uptrend_mask = direction == 1.0
    uptrend_index = direction[uptrend_mask].index
    assert (result.loc[uptrend_index, "supertrend"] < df.loc[uptrend_index, "close"]).all()


def test_williams_r_bounded_between_minus_100_and_0(ohlcv_df):
    result = indicator_registry.get("williams_r").compute(ohlcv_df, window=14)
    valid = result["williams_r"].dropna()
    assert (valid >= -100.01).all() and (valid <= 0.01).all()


def test_cci_matches_manual_calculation():
    dates = pd.bdate_range("2023-01-02", periods=30)
    close = [100 + (i % 5) for i in range(30)]
    df = pd.DataFrame(
        {"open": close, "high": close, "low": close, "close": close, "volume": [1_000.0] * 30}, index=dates
    )
    result = indicator_registry.get("cci").compute(df, window=10)
    # constant-range OHLC -> typical price == close; verify against a manual rolling calc for one row.
    tp = df["close"]
    window = tp.iloc[10:20]
    sma = window.mean()
    mad = (window - window.mean()).abs().mean()
    expected = (tp.iloc[19] - sma) / (0.015 * mad) if mad else 0.0
    assert result["cci"].iloc[19] == pytest.approx(expected, rel=1e-6)


def test_aroon_up_is_100_at_a_fresh_high():
    dates = pd.bdate_range("2023-01-02", periods=30)
    close = list(range(1, 31))  # strictly increasing -> today is always the highest high
    df = pd.DataFrame(
        {"open": close, "high": close, "low": close, "close": close, "volume": [1_000.0] * 30}, index=dates
    )
    result = indicator_registry.get("aroon").compute(df, window=10)
    assert result["aroon_up"].iloc[-1] == pytest.approx(100.0)
    assert result["aroon_down"].iloc[-1] == pytest.approx(0.0)


def test_parabolic_sar_direction_is_plus_or_minus_one(ohlcv_df):
    result = indicator_registry.get("parabolic_sar").compute(ohlcv_df)
    valid = result["parabolic_sar_direction"].dropna()
    assert set(valid.unique()) <= {1.0, -1.0}


def test_parabolic_sar_stays_below_close_in_a_steady_uptrend():
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
    result = indicator_registry.get("parabolic_sar").compute(df)
    tail = result.iloc[-5:]
    assert (tail["parabolic_sar_direction"] == 1.0).all()
    assert (tail["parabolic_sar"] < df["close"].iloc[-5:]).all()


def test_obv_increases_on_up_days_and_decreases_on_down_days():
    dates = pd.bdate_range("2023-01-02", periods=5)
    df = pd.DataFrame(
        {
            "open": [100, 101, 99, 98, 100],
            "high": [100, 101, 99, 98, 100],
            "low": [100, 101, 99, 98, 100],
            "close": [100, 101, 99, 98, 100],
            "volume": [1000.0, 500.0, 300.0, 200.0, 400.0],
        },
        index=dates,
    )
    result = indicator_registry.get("obv").compute(df)
    # day2 up +500, day3 down -300, day4 down -200, day5 up +400
    assert result["obv"].tolist() == pytest.approx([0.0, 500.0, 200.0, 0.0, 400.0])


def test_mfi_bounded_between_0_and_100(ohlcv_df):
    result = indicator_registry.get("mfi").compute(ohlcv_df, window=14)
    valid = result["mfi"].dropna()
    assert (valid >= 0).all() and (valid <= 100).all()


def test_unknown_indicator_raises_key_error():
    with pytest.raises(KeyError):
        indicator_registry.get("not_a_real_indicator")
