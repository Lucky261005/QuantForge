import pandas as pd

from app.core.params import ParamSpec
from app.indicators import indicator_registry
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class ParabolicSARTrendStrategy(Strategy):
    key = "parabolic_sar_trend"
    label = "Parabolic SAR Trend"
    description = (
        "Long while Wilder's Parabolic SAR dots sit below price (confirmed uptrend), flat "
        "(or short, if enabled) while they sit above — a classic trailing-stop-style trend "
        "filter that tightens automatically as a trend extends."
    )
    param_specs = [
        ParamSpec("af_start", "float", 0.02, 0.005, 0.1),
        ParamSpec("af_step", "float", 0.02, 0.005, 0.1),
        ParamSpec("af_max", "float", 0.2, 0.05, 0.5),
        ParamSpec("allow_short", "int", 0, 0, 1),
    ]

    def generate_signals(
        self,
        df: pd.DataFrame,
        af_start: float = 0.02,
        af_step: float = 0.02,
        af_max: float = 0.2,
        allow_short: int = 0,
        **_,
    ) -> pd.Series:
        result = indicator_registry.get("parabolic_sar").compute(df, af_start=af_start, af_step=af_step, af_max=af_max)
        signal = pd.Series(0.0, index=df.index)
        signal[result["parabolic_sar_direction"] == 1.0] = 1.0
        if allow_short:
            signal[result["parabolic_sar_direction"] == -1.0] = -1.0
        return signal
