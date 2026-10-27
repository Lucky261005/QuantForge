import numpy as np
import pandas as pd

from app.core.params import ParamSpec
from app.indicators import indicator_registry
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class RSIMeanReversionStrategy(Strategy):
    key = "rsi_mean_reversion"
    label = "RSI Reversal (Mean Reversion)"
    description = (
        "Enters long when RSI drops below the oversold threshold (expecting a bounce), "
        "exits back to flat once RSI recovers above the overbought threshold."
    )
    param_specs = [
        ParamSpec("window", "int", 14, 2, 100),
        ParamSpec("oversold", "float", 30, 5, 45),
        ParamSpec("overbought", "float", 70, 55, 95),
    ]

    def generate_signals(
        self, df: pd.DataFrame, window: int = 14, oversold: float = 30, overbought: float = 70, **_
    ) -> pd.Series:
        rsi = indicator_registry.get("rsi").compute(df, window=window)["rsi"]

        signal = pd.Series(np.nan, index=df.index)
        signal[rsi < oversold] = 1.0
        signal[rsi > overbought] = 0.0
        return signal.ffill().fillna(0.0)
