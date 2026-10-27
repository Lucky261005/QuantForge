import pandas as pd

from app.core.params import ParamSpec
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class MomentumStrategy(Strategy):
    key = "momentum"
    label = "Time-Series Momentum"
    description = "Long when the trailing N-day return is positive, flat otherwise — classic time-series momentum."
    param_specs = [ParamSpec("lookback", "int", 90, 5, 500)]

    def generate_signals(self, df: pd.DataFrame, lookback: int = 90, **_) -> pd.Series:
        trailing_return = df["close"].pct_change(periods=lookback)
        return (trailing_return > 0).astype(float)
