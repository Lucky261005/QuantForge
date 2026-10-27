import numpy as np
import pandas as pd

from app.core.params import ParamSpec
from app.indicators import indicator_registry
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class WilliamsRReversalStrategy(Strategy):
    key = "williams_r_reversal"
    label = "Williams %R Reversal"
    description = (
        "Enters long when Williams %R drops below the oversold threshold (deeply oversold), "
        "exits back to flat once it recovers above the overbought threshold — the same "
        "reversal logic as RSI, on a different (0 to -100) scale."
    )
    param_specs = [
        ParamSpec("window", "int", 14, 2, 200),
        ParamSpec("oversold", "float", -80, -95, -55),
        ParamSpec("overbought", "float", -20, -45, -5),
    ]

    def generate_signals(
        self, df: pd.DataFrame, window: int = 14, oversold: float = -80, overbought: float = -20, **_
    ) -> pd.Series:
        wr = indicator_registry.get("williams_r").compute(df, window=window)["williams_r"]

        signal = pd.Series(np.nan, index=df.index)
        signal[wr < oversold] = 1.0
        signal[wr > overbought] = 0.0
        return signal.ffill().fillna(0.0)
