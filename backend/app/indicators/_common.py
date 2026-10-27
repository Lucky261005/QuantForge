"""Shared helpers used by multiple indicators — kept private (leading underscore)
since callers should only ever go through the registry."""

import pandas as pd


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    ranges = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    )
    return ranges.max(axis=1)


def wilder_smooth(series: pd.Series, window: int) -> pd.Series:
    """Wilder's smoothing (used by ATR/ADX/RSI) — an EMA variant with alpha = 1/window."""
    return series.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
