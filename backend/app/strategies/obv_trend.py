import pandas as pd

from app.core.params import ParamSpec
from app.indicators import indicator_registry
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class OBVTrendStrategy(Strategy):
    key = "obv_trend"
    label = "OBV Trend Confirmation"
    description = (
        "Long while On-Balance Volume is above its own moving average (accumulation — volume "
        "confirming the price trend), flat while below — a volume-confirmation filter rather "
        "than a price-pattern signal."
    )
    param_specs = [ParamSpec("smoothing_window", "int", 20, 2, 200)]

    def generate_signals(self, df: pd.DataFrame, smoothing_window: int = 20, **_) -> pd.Series:
        obv = indicator_registry.get("obv").compute(df)["obv"]
        obv_ma = obv.rolling(window=smoothing_window, min_periods=smoothing_window).mean()
        return (obv > obv_ma).astype(float)
