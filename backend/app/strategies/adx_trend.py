import pandas as pd

from app.core.params import ParamSpec
from app.indicators import indicator_registry
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class ADXTrendStrategy(Strategy):
    key = "adx_trend"
    label = "ADX Trend"
    description = (
        "Long only while ADX is above a strength threshold and +DI is above -DI — a strong, "
        "already-established uptrend — flat otherwise. Filters out the choppy, range-bound "
        "conditions that whipsaw a plain moving-average crossover."
    )
    param_specs = [
        ParamSpec("window", "int", 14, 2, 100),
        ParamSpec("adx_threshold", "float", 25.0, 5.0, 60.0),
    ]

    def generate_signals(self, df: pd.DataFrame, window: int = 14, adx_threshold: float = 25.0, **_) -> pd.Series:
        result = indicator_registry.get("adx").compute(df, window=window)
        strong_uptrend = (result["adx"] > adx_threshold) & (result["di_plus"] > result["di_minus"])
        return strong_uptrend.astype(float)
