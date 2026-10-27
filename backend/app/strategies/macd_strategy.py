import pandas as pd

from app.core.params import ParamSpec
from app.indicators import indicator_registry
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class MACDCrossoverStrategy(Strategy):
    key = "macd"
    label = "MACD Crossover"
    description = "Long when the MACD line is above its signal line, flat when it is below."
    param_specs = [
        ParamSpec("fast_period", "int", 12, 2, 200),
        ParamSpec("slow_period", "int", 26, 2, 400),
        ParamSpec("signal_period", "int", 9, 2, 100),
    ]

    def generate_signals(
        self, df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, **_
    ) -> pd.Series:
        result = indicator_registry.get("macd").compute(
            df, fast_period=fast_period, slow_period=slow_period, signal_period=signal_period
        )
        return (result["macd"] > result["macd_signal"]).astype(float)
