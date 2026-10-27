import numpy as np
import pandas as pd

from app.indicators._common import true_range, wilder_smooth
from app.indicators.registry import ParamSpec, register_indicator


@register_indicator("sma", "Simple Moving Average", ["sma"], [ParamSpec("window", "int", 20, 2, 500)])
def sma(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    return pd.DataFrame({"sma": df["close"].rolling(window=window, min_periods=window).mean()})


@register_indicator("ema", "Exponential Moving Average", ["ema"], [ParamSpec("window", "int", 20, 2, 500)])
def ema(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    return pd.DataFrame({"ema": df["close"].ewm(span=window, adjust=False, min_periods=window).mean()})


@register_indicator(
    "macd",
    "MACD",
    ["macd", "macd_signal", "macd_hist"],
    [
        ParamSpec("fast_period", "int", 12, 2, 200),
        ParamSpec("slow_period", "int", 26, 2, 400),
        ParamSpec("signal_period", "int", 9, 2, 100),
    ],
)
def macd(df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
    fast_ema = df["close"].ewm(span=fast_period, adjust=False).mean()
    slow_ema = df["close"].ewm(span=slow_period, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    return pd.DataFrame({"macd": macd_line, "macd_signal": signal_line, "macd_hist": macd_line - signal_line})


@register_indicator(
    "adx",
    "Average Directional Index",
    ["adx", "di_plus", "di_minus"],
    [ParamSpec("window", "int", 14, 2, 100)],
)
def adx(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    up_move = df["high"].diff()
    down_move = -df["low"].diff()

    plus_dm = pd.Series(0.0, index=df.index)
    minus_dm = pd.Series(0.0, index=df.index)
    plus_dm[(up_move > down_move) & (up_move > 0)] = up_move[(up_move > down_move) & (up_move > 0)]
    minus_dm[(down_move > up_move) & (down_move > 0)] = down_move[(down_move > up_move) & (down_move > 0)]

    atr = wilder_smooth(true_range(df), window)
    di_plus = 100 * wilder_smooth(plus_dm, window) / atr
    di_minus = 100 * wilder_smooth(minus_dm, window) / atr
    dx = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus)
    adx_line = wilder_smooth(dx, window)

    return pd.DataFrame({"adx": adx_line, "di_plus": di_plus, "di_minus": di_minus})


@register_indicator(
    "supertrend",
    "SuperTrend",
    ["supertrend", "supertrend_direction"],
    [ParamSpec("window", "int", 10, 2, 100), ParamSpec("multiplier", "float", 3.0, 0.5, 10.0)],
)
def supertrend(df: pd.DataFrame, window: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    """A widely used NSE-cash/F&O trend-following overlay. Direction flips are path
    dependent (each band depends on whether the prior close breached it), so — unlike
    the other indicators here — this needs a row-by-row pass rather than a pure
    vectorized rolling computation."""
    atr_line = wilder_smooth(true_range(df), window)
    hl2 = (df["high"] + df["low"]) / 2
    basic_upper = (hl2 + multiplier * atr_line).to_numpy()
    basic_lower = (hl2 - multiplier * atr_line).to_numpy()
    close = df["close"].to_numpy()

    n = len(df)
    final_upper = np.full(n, np.nan)
    final_lower = np.full(n, np.nan)
    direction = np.zeros(n)  # +1 uptrend (price above the line), -1 downtrend

    start = window  # first `window` bars have no ATR yet
    for t in range(start, n):
        final_upper[t] = (
            basic_upper[t]
            if t == start or basic_upper[t] < final_upper[t - 1] or close[t - 1] > final_upper[t - 1]
            else final_upper[t - 1]
        )
        final_lower[t] = (
            basic_lower[t]
            if t == start or basic_lower[t] > final_lower[t - 1] or close[t - 1] < final_lower[t - 1]
            else final_lower[t - 1]
        )

        if t == start:
            direction[t] = 1.0 if close[t] > final_upper[t] else -1.0
        elif direction[t - 1] == 1.0:
            direction[t] = -1.0 if close[t] < final_lower[t] else 1.0
        else:
            direction[t] = 1.0 if close[t] > final_upper[t] else -1.0

    supertrend_line = np.where(direction == 1.0, final_lower, final_upper)
    supertrend_line[:start] = np.nan
    direction[:start] = np.nan

    return pd.DataFrame({"supertrend": supertrend_line, "supertrend_direction": direction}, index=df.index)


@register_indicator(
    "aroon",
    "Aroon",
    ["aroon_up", "aroon_down"],
    [ParamSpec("window", "int", 25, 2, 200)],
)
def aroon(df: pd.DataFrame, window: int = 25) -> pd.DataFrame:
    periods_since_high = df["high"].rolling(window=window + 1).apply(lambda s: window - s.argmax(), raw=True)
    periods_since_low = df["low"].rolling(window=window + 1).apply(lambda s: window - s.argmin(), raw=True)
    aroon_up = 100 * (window - periods_since_high) / window
    aroon_down = 100 * (window - periods_since_low) / window
    return pd.DataFrame({"aroon_up": aroon_up, "aroon_down": aroon_down})


@register_indicator(
    "parabolic_sar",
    "Parabolic SAR",
    ["parabolic_sar", "parabolic_sar_direction"],
    [
        ParamSpec("af_start", "float", 0.02, 0.005, 0.1),
        ParamSpec("af_step", "float", 0.02, 0.005, 0.1),
        ParamSpec("af_max", "float", 0.2, 0.05, 0.5),
    ],
)
def parabolic_sar(df: pd.DataFrame, af_start: float = 0.02, af_step: float = 0.02, af_max: float = 0.2) -> pd.DataFrame:
    """Wilder's Parabolic SAR — path dependent (each dot depends on the prior dot,
    acceleration factor, and extreme point), so like SuperTrend this needs a
    row-by-row pass rather than a vectorized rolling computation."""
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    n = len(df)

    sar = np.full(n, np.nan)
    direction = np.zeros(n)  # +1 uptrend, -1 downtrend
    if n < 2:
        return pd.DataFrame({"parabolic_sar": sar, "parabolic_sar_direction": direction}, index=df.index)

    is_uptrend = high[1] >= high[0]
    sar[0] = low[0] if is_uptrend else high[0]
    direction[0] = 1.0 if is_uptrend else -1.0
    ep = high[0] if is_uptrend else low[0]
    af = af_start

    for t in range(1, n):
        prev_sar = sar[t - 1]
        candidate_sar = prev_sar + af * (ep - prev_sar)

        if is_uptrend:
            candidate_sar = min(candidate_sar, low[t - 1], low[t - 2] if t >= 2 else low[t - 1])
            if low[t] < candidate_sar:
                is_uptrend = False
                sar[t] = ep
                ep = low[t]
                af = af_start
            else:
                sar[t] = candidate_sar
                if high[t] > ep:
                    ep = high[t]
                    af = min(af + af_step, af_max)
        else:
            candidate_sar = max(candidate_sar, high[t - 1], high[t - 2] if t >= 2 else high[t - 1])
            if high[t] > candidate_sar:
                is_uptrend = True
                sar[t] = ep
                ep = high[t]
                af = af_start
            else:
                sar[t] = candidate_sar
                if low[t] < ep:
                    ep = low[t]
                    af = min(af + af_step, af_max)

        direction[t] = 1.0 if is_uptrend else -1.0

    return pd.DataFrame({"parabolic_sar": sar, "parabolic_sar_direction": direction}, index=df.index)
