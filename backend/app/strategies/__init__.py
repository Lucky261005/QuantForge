"""Import every strategy module so its @register_strategy decorators run before
anything queries the registry."""

from app.strategies import (  # noqa: F401
    adx_trend,
    aroon_trend,
    bollinger_breakout,
    bollinger_zscore_reversion,
    buy_and_hold,
    cci_trend,
    donchian_breakout,
    ema_crossover,
    ma_ribbon,
    macd_strategy,
    mfi_reversal,
    momentum,
    moving_average,
    obv_trend,
    opening_range_breakout,
    parabolic_sar_trend,
    rsi_mean_reversion,
    stochastic_reversal,
    supertrend_strategy,
    vwap_strategy,
    williams_r_reversal,
)
from app.strategies.base import Strategy
from app.strategies.registry import StrategyRegistry, strategy_registry

__all__ = ["Strategy", "StrategyRegistry", "strategy_registry"]
