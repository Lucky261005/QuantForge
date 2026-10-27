import pandas as pd

from app.indicators import indicator_registry
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class VWAPTrendStrategy(Strategy):
    key = "vwap_trend"
    label = "VWAP Intraday Trend"
    description = (
        "Long while price trades above the cumulative VWAP, flat while below — a simple trend "
        "filter anchored to volume-weighted fair value, the same reference line NSE intraday "
        "traders watch on Kite/TradingView. VWAP resets are the caller's responsibility for a "
        "true per-session intraday VWAP; on daily bars this runs as a full-history VWAP."
    )
    param_specs = []

    def generate_signals(self, df: pd.DataFrame, **_) -> pd.Series:
        vwap = indicator_registry.get("vwap").compute(df)["vwap"]
        return (df["close"] > vwap).astype(float)
