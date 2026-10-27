"""Import every indicator module so its @register_indicator decorators run and
populate the IndicatorRegistry before anything queries it."""

from app.indicators import momentum, trend, volatility, volume  # noqa: F401
from app.indicators.registry import IndicatorRegistry, indicator_registry

__all__ = ["IndicatorRegistry", "indicator_registry"]
