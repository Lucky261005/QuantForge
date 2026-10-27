import pandas as pd

from app.indicators._common import wilder_smooth
from app.indicators.registry import ParamSpec, register_indicator


@register_indicator("rsi", "Relative Strength Index", ["rsi"], [ParamSpec("window", "int", 14, 2, 200)])
def rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    delta = df["close"].diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    avg_gain = wilder_smooth(gains, window)
    avg_loss = wilder_smooth(losses, window)

    rs = avg_gain / avg_loss
    rsi_line = 100 - (100 / (1 + rs))
    rsi_line = rsi_line.where(avg_loss != 0, 100.0)
    return pd.DataFrame({"rsi": rsi_line})


@register_indicator(
    "stochastic",
    "Stochastic Oscillator",
    ["stoch_k", "stoch_d"],
    [ParamSpec("k_period", "int", 14, 2, 100), ParamSpec("d_period", "int", 3, 1, 50)],
)
def stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
    lowest_low = df["low"].rolling(window=k_period, min_periods=k_period).min()
    highest_high = df["high"].rolling(window=k_period, min_periods=k_period).max()
    stoch_k = 100 * (df["close"] - lowest_low) / (highest_high - lowest_low)
    stoch_d = stoch_k.rolling(window=d_period, min_periods=d_period).mean()
    return pd.DataFrame({"stoch_k": stoch_k, "stoch_d": stoch_d})


@register_indicator("roc", "Rate of Change", ["roc"], [ParamSpec("window", "int", 12, 1, 300)])
def roc(df: pd.DataFrame, window: int = 12) -> pd.DataFrame:
    return pd.DataFrame({"roc": 100 * (df["close"] - df["close"].shift(window)) / df["close"].shift(window)})


@register_indicator("williams_r", "Williams %R", ["williams_r"], [ParamSpec("window", "int", 14, 2, 200)])
def williams_r(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    highest_high = df["high"].rolling(window=window, min_periods=window).max()
    lowest_low = df["low"].rolling(window=window, min_periods=window).min()
    wr = -100 * (highest_high - df["close"]) / (highest_high - lowest_low)
    return pd.DataFrame({"williams_r": wr})


@register_indicator("cci", "Commodity Channel Index", ["cci"], [ParamSpec("window", "int", 20, 2, 200)])
def cci(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    sma_tp = typical_price.rolling(window=window, min_periods=window).mean()
    mean_abs_dev = typical_price.rolling(window=window, min_periods=window).apply(
        lambda s: (s - s.mean()).abs().mean(), raw=False
    )
    cci_line = (typical_price - sma_tp) / (0.015 * mean_abs_dev)
    return pd.DataFrame({"cci": cci_line})
