import pandas as pd

from app.indicators._common import true_range, wilder_smooth
from app.indicators.registry import ParamSpec, register_indicator


@register_indicator(
    "bollinger_bands",
    "Bollinger Bands",
    ["bb_middle", "bb_upper", "bb_lower"],
    [ParamSpec("window", "int", 20, 2, 200), ParamSpec("num_std", "float", 2.0, 0.5, 5.0)],
)
def bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    middle = df["close"].rolling(window=window, min_periods=window).mean()
    std = df["close"].rolling(window=window, min_periods=window).std()
    return pd.DataFrame({"bb_middle": middle, "bb_upper": middle + num_std * std, "bb_lower": middle - num_std * std})


@register_indicator("atr", "Average True Range", ["atr"], [ParamSpec("window", "int", 14, 2, 200)])
def atr(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    return pd.DataFrame({"atr": wilder_smooth(true_range(df), window)})
