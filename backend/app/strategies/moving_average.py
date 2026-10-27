import pandas as pd

from app.core.params import ParamSpec
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class MovingAverageCrossStrategy(Strategy):
    key = "ma_cross"
    label = "Golden Cross / Death Cross (MA Crossover)"
    description = (
        "Long while the fast SMA is above the slow SMA, flat (or short, if enabled) otherwise. "
        "The classic 50/200 setting reproduces the golden cross (bullish) / death cross (bearish) signal."
    )
    param_specs = [
        ParamSpec("fast_window", "int", 50, 2, 300),
        ParamSpec("slow_window", "int", 200, 5, 500),
        ParamSpec("allow_short", "int", 0, 0, 1),
    ]

    def generate_signals(
        self, df: pd.DataFrame, fast_window: int = 50, slow_window: int = 200, allow_short: int = 0, **_
    ) -> pd.Series:
        fast = df["close"].rolling(window=fast_window, min_periods=fast_window).mean()
        slow = df["close"].rolling(window=slow_window, min_periods=slow_window).mean()

        signal = pd.Series(0.0, index=df.index)
        signal[fast > slow] = 1.0
        if allow_short:
            signal[fast < slow] = -1.0
        return signal
