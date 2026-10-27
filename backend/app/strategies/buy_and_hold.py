import pandas as pd

from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class BuyAndHoldStrategy(Strategy):
    key = "buy_and_hold"
    label = "Buy & Hold"
    description = "Goes long on day one and holds for the entire backtest period — the standard passive benchmark."
    param_specs = []

    def generate_signals(self, df: pd.DataFrame, **params) -> pd.Series:
        return pd.Series(1, index=df.index, dtype=float)
