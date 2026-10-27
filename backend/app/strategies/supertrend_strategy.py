import pandas as pd

from app.core.params import ParamSpec
from app.indicators import indicator_registry
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class SuperTrendStrategy(Strategy):
    key = "supertrend"
    label = "SuperTrend"
    description = (
        "Long while price is in a confirmed SuperTrend uptrend, flat (or short, if enabled) "
        "during a downtrend — a volatility-adjusted trend filter widely used on NSE cash and "
        "F&O charts, less prone to whipsaws than a plain moving-average cross in choppy markets."
    )
    param_specs = [
        ParamSpec("window", "int", 10, 2, 100),
        ParamSpec("multiplier", "float", 3.0, 0.5, 10.0),
        ParamSpec("allow_short", "int", 0, 0, 1),
    ]

    def generate_signals(
        self, df: pd.DataFrame, window: int = 10, multiplier: float = 3.0, allow_short: int = 0, **_
    ) -> pd.Series:
        result = indicator_registry.get("supertrend").compute(df, window=window, multiplier=multiplier)

        signal = pd.Series(0.0, index=df.index)
        signal[result["supertrend_direction"] == 1.0] = 1.0
        if allow_short:
            signal[result["supertrend_direction"] == -1.0] = -1.0
        return signal
