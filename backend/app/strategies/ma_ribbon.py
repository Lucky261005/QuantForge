import pandas as pd

from app.core.params import ParamSpec
from app.strategies.base import Strategy
from app.strategies.registry import register_strategy


@register_strategy
class MovingAverageRibbonStrategy(Strategy):
    key = "ma_ribbon"
    label = "Moving Average Ribbon"
    description = (
        "Long only when a stack of five SMAs (fastest to slowest) is fully aligned bullish "
        "(each faster average above the next slower one) — a stricter trend-confirmation "
        "filter than a single crossover, common on NSE swing-trading ribbon charts."
    )
    param_specs = [
        ParamSpec("w1", "int", 10, 2, 100),
        ParamSpec("w2", "int", 20, 2, 150),
        ParamSpec("w3", "int", 30, 2, 200),
        ParamSpec("w4", "int", 50, 2, 300),
        ParamSpec("w5", "int", 100, 2, 400),
    ]

    def generate_signals(
        self, df: pd.DataFrame, w1: int = 10, w2: int = 20, w3: int = 30, w4: int = 50, w5: int = 100, **_
    ) -> pd.Series:
        mas = [df["close"].rolling(window=w, min_periods=w).mean() for w in (w1, w2, w3, w4, w5)]
        bullish = (mas[0] > mas[1]) & (mas[1] > mas[2]) & (mas[2] > mas[3]) & (mas[3] > mas[4])
        return bullish.astype(float)
