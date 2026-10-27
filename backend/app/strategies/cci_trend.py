import pandas as pd

from app.core.params import ParamSpec
from app.indicators import indicator_registry
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class CCITrendStrategy(Strategy):
    key = "cci_trend"
    label = "CCI Trend"
    description = (
        "Long while the Commodity Channel Index is above its breakout threshold (a strong "
        "momentum move away from the typical-price average), flat once it falls back below."
    )
    param_specs = [
        ParamSpec("window", "int", 20, 2, 200),
        ParamSpec("threshold", "float", 100.0, 50.0, 200.0),
    ]

    def generate_signals(self, df: pd.DataFrame, window: int = 20, threshold: float = 100.0, **_) -> pd.Series:
        cci = indicator_registry.get("cci").compute(df, window=window)["cci"]
        return (cci > threshold).astype(float)
