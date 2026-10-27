"""MarketDataProvider — the seam that lets QuantForge swap data sources without
touching any caller. Every provider returns the same normalized OHLCV shape."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class OhlcvBar:
    date: date
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: float


class MarketDataProvider(ABC):
    """Implement this for any new data source. `fetch_ohlcv` must raise
    `ExternalServiceError` (not a provider-specific exception) on failure so the
    service layer never has to know which provider is behind the interface."""

    name: str

    @abstractmethod
    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> list[OhlcvBar]: ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Whether this provider has the credentials it needs to run for real."""
        ...
