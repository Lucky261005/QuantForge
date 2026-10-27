import pandas as pd

from app.core.params import ParamSpec
from app.indicators import indicator_registry
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class EMACrossoverStrategy(Strategy):
    key = "ema_crossover"
    label = "EMA Crossover"
    description = (
        "Long while the fast EMA is above the slow EMA, flat (or short, if enabled) otherwise — "
        "the EMA analogue of the classic moving average cross, reacting faster to recent price "
        "action than an SMA cross since EMA weights recent bars more heavily."
    )
    param_specs = [
        ParamSpec("fast_window", "int", 9, 2, 100),
        ParamSpec("slow_window", "int", 21, 5, 300),
        ParamSpec("allow_short", "int", 0, 0, 1),
    ]

    def generate_signals(
        self, df: pd.DataFrame, fast_window: int = 9, slow_window: int = 21, allow_short: int = 0, **_
    ) -> pd.Series:
        fast = indicator_registry.get("ema").compute(df, window=fast_window)["ema"]
        slow = indicator_registry.get("ema").compute(df, window=slow_window)["ema"]

        signal = pd.Series(0.0, index=df.index)
        signal[fast > slow] = 1.0
        if allow_short:
            signal[fast < slow] = -1.0
        return signal
