import pandas as pd

from app.core.params import ParamSpec
from app.indicators import indicator_registry
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class AroonTrendStrategy(Strategy):
    key = "aroon_trend"
    label = "Aroon Trend"
    description = (
        "Long while Aroon Up leads Aroon Down and Aroon Up is above its strength threshold "
        "(a fresh, dominant uptrend), flat otherwise."
    )
    param_specs = [
        ParamSpec("window", "int", 25, 2, 200),
        ParamSpec("threshold", "float", 70.0, 50.0, 95.0),
    ]

    def generate_signals(self, df: pd.DataFrame, window: int = 25, threshold: float = 70.0, **_) -> pd.Series:
        result = indicator_registry.get("aroon").compute(df, window=window)
        strong_uptrend = (result["aroon_up"] > result["aroon_down"]) & (result["aroon_up"] > threshold)
        return strong_uptrend.astype(float)
