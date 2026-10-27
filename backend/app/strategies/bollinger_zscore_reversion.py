import numpy as np
import pandas as pd

from app.core.params import ParamSpec
from app.indicators import indicator_registry
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class BollingerZScoreReversionStrategy(Strategy):
    key = "bollinger_zscore_reversion"
    label = "Bollinger Mean Reversion (Z-Score)"
    description = (
        "Long when price's z-score relative to its Bollinger mean drops below a negative "
        "entry threshold (statistically stretched to the downside), exits back to flat once "
        "the z-score recovers to zero — a mean-reversion read of the same bands "
        "'Bollinger Breakout' trades as a momentum signal."
    )
    param_specs = [
        ParamSpec("window", "int", 20, 2, 200),
        ParamSpec("entry_z", "float", -2.0, -4.0, -0.5),
    ]

    def generate_signals(self, df: pd.DataFrame, window: int = 20, entry_z: float = -2.0, **_) -> pd.Series:
        bands = indicator_registry.get("bollinger_bands").compute(df, window=window, num_std=1.0)
        std = bands["bb_upper"] - bands["bb_middle"]  # num_std=1.0, so this equals the raw rolling std
        z_score = (df["close"] - bands["bb_middle"]) / std

        signal = pd.Series(np.nan, index=df.index)
        signal[z_score < entry_z] = 1.0
        signal[z_score >= 0] = 0.0
        return signal.ffill().fillna(0.0)
