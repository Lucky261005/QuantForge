import numpy as np
import pandas as pd

from app.core.params import ParamSpec
from app.indicators import indicator_registry
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class BollingerBreakoutStrategy(Strategy):
    key = "bollinger_breakout"
    label = "Bollinger Band Breakout"
    description = (
        "Long when price closes above the upper Bollinger Band (volatility breakout), "
        "exits back to flat once price falls back below the middle band."
    )
    param_specs = [
        ParamSpec("window", "int", 20, 2, 200),
        ParamSpec("num_std", "float", 2.0, 0.5, 5.0),
    ]

    def generate_signals(self, df: pd.DataFrame, window: int = 20, num_std: float = 2.0, **_) -> pd.Series:
        bands = indicator_registry.get("bollinger_bands").compute(df, window=window, num_std=num_std)

        signal = pd.Series(np.nan, index=df.index)
        signal[df["close"] > bands["bb_upper"]] = 1.0
        signal[df["close"] < bands["bb_middle"]] = 0.0
        return signal.ffill().fillna(0.0)
