import numpy as np
import pandas as pd

from app.core.params import ParamSpec
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class DonchianBreakoutStrategy(Strategy):
    key = "donchian_breakout"
    label = "Swing Breakout (Donchian Channel)"
    description = (
        "Long on a new N-day high (channel breakout), exits back to flat on a new M-day low — "
        "the classic turtle-trading breakout system."
    )
    param_specs = [
        ParamSpec("entry_window", "int", 20, 5, 200),
        ParamSpec("exit_window", "int", 10, 5, 200),
    ]

    def generate_signals(self, df: pd.DataFrame, entry_window: int = 20, exit_window: int = 10, **_) -> pd.Series:
        upper_channel = df["high"].rolling(window=entry_window, min_periods=entry_window).max().shift(1)
        lower_channel = df["low"].rolling(window=exit_window, min_periods=exit_window).min().shift(1)

        signal = pd.Series(np.nan, index=df.index)
        signal[df["close"] > upper_channel] = 1.0
        signal[df["close"] < lower_channel] = 0.0
        return signal.ffill().fillna(0.0)
