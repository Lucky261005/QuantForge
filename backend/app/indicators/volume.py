import numpy as np
import pandas as pd

from app.indicators.registry import ParamSpec, register_indicator


@register_indicator("vwap", "Volume Weighted Average Price", ["vwap"], [])
def vwap(df: pd.DataFrame) -> pd.DataFrame:
    """Cumulative VWAP over the full series (resets are the caller's responsibility
    if a per-session VWAP is needed for intraday data)."""
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    cum_vol = df["volume"].cumsum()
    cum_vol_price = (typical_price * df["volume"]).cumsum()
    return pd.DataFrame({"vwap": cum_vol_price / cum_vol})


@register_indicator("obv", "On-Balance Volume", ["obv"], [])
def obv(df: pd.DataFrame) -> pd.DataFrame:
    direction = np.sign(df["close"].diff().fillna(0.0))
    return pd.DataFrame({"obv": (direction * df["volume"]).cumsum()})


@register_indicator(
    "mfi",
    "Money Flow Index",
    ["mfi"],
    [ParamSpec("window", "int", 14, 2, 100)],
)
def mfi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """Volume-weighted RSI analogue — same overbought/oversold reading as RSI but
    weighted by money flow (typical price * volume) instead of price alone."""
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    raw_money_flow = typical_price * df["volume"]
    price_up = typical_price.diff() > 0

    positive_flow = raw_money_flow.where(price_up, 0.0).rolling(window=window, min_periods=window).sum()
    negative_flow = raw_money_flow.where(~price_up, 0.0).rolling(window=window, min_periods=window).sum()

    money_ratio = positive_flow / negative_flow
    mfi_line = 100 - (100 / (1 + money_ratio))
    mfi_line = mfi_line.where(negative_flow != 0, 100.0)
    return pd.DataFrame({"mfi": mfi_line})
