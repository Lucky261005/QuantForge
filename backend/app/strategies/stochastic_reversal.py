import numpy as np
import pandas as pd

from app.core.params import ParamSpec
from app.indicators import indicator_registry
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class StochasticReversalStrategy(Strategy):
    key = "stochastic_reversal"
    label = "Stochastic Reversal"
    description = (
        "Enters long when the %K stochastic line drops below the oversold threshold, exits "
        "back to flat once it recovers above the overbought threshold — the same reversal "
        "shape as RSI/Williams %R, on a %K/%D-smoothed oscillator."
    )
    param_specs = [
        ParamSpec("k_period", "int", 14, 2, 100),
        ParamSpec("d_period", "int", 3, 1, 50),
        ParamSpec("oversold", "float", 20, 5, 40),
        ParamSpec("overbought", "float", 80, 60, 95),
    ]

    def generate_signals(
        self,
        df: pd.DataFrame,
        k_period: int = 14,
        d_period: int = 3,
        oversold: float = 20,
        overbought: float = 80,
        **_,
    ) -> pd.Series:
        stoch_k = indicator_registry.get("stochastic").compute(df, k_period=k_period, d_period=d_period)["stoch_k"]

        signal = pd.Series(np.nan, index=df.index)
        signal[stoch_k < oversold] = 1.0
        signal[stoch_k > overbought] = 0.0
        return signal.ffill().fillna(0.0)
