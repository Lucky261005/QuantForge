import numpy as np
import pandas as pd

from app.core.params import ParamSpec
from app.indicators import indicator_registry
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class MFIReversalStrategy(Strategy):
    key = "mfi_reversal"
    label = "Money Flow Index Reversal"
    description = (
        "Enters long when the Money Flow Index drops below the oversold threshold (selling "
        "pressure exhausted on volume, not just price), exits back to flat once it recovers "
        "above the overbought threshold."
    )
    param_specs = [
        ParamSpec("window", "int", 14, 2, 100),
        ParamSpec("oversold", "float", 20, 5, 40),
        ParamSpec("overbought", "float", 80, 60, 95),
    ]

    def generate_signals(
        self, df: pd.DataFrame, window: int = 14, oversold: float = 20, overbought: float = 80, **_
    ) -> pd.Series:
        mfi = indicator_registry.get("mfi").compute(df, window=window)["mfi"]

        signal = pd.Series(np.nan, index=df.index)
        signal[mfi < oversold] = 1.0
        signal[mfi > overbought] = 0.0
        return signal.ffill().fillna(0.0)
