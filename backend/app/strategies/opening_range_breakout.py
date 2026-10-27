import numpy as np
import pandas as pd

from app.core.params import ParamSpec
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class OpeningRangeBreakoutStrategy(Strategy):
    key = "orb"
    label = "Opening Range Breakout"
    description = (
        "Long once price closes above the high of the first `range_bars` bars of each session, "
        "flat once price closes back below that session's opening-range low. Session boundaries "
        "are inferred from calendar date, so this is only meaningful on intraday bars (5m/15m/30m/"
        "1h) — on daily bars each session is a single bar, the opening range collapses to that "
        "bar's own range, and no trades will be generated. See docs/ARCHITECTURE.md §7 for the "
        "intraday-data extension seam."
    )
    param_specs = [ParamSpec("range_bars", "int", 1, 1, 50)]

    def generate_signals(self, df: pd.DataFrame, range_bars: int = 1, **_) -> pd.Series:
        day_key = pd.Series(df.index.date if hasattr(df.index, "date") else df.index.values, index=df.index)
        bar_rank = day_key.groupby(day_key).cumcount()

        range_high = df.groupby(day_key)["high"].transform(lambda s: s.iloc[:range_bars].max())
        range_low = df.groupby(day_key)["low"].transform(lambda s: s.iloc[:range_bars].min())

        signal = pd.Series(np.nan, index=df.index)
        signal[bar_rank == 0] = 0.0  # flat at the start of every new session
        after_range = bar_rank >= range_bars
        signal[after_range & (df["close"] > range_high)] = 1.0
        signal[after_range & (df["close"] < range_low)] = 0.0
        return signal.ffill().fillna(0.0)
