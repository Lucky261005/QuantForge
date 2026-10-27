"""Polygon.io provider — real implementation, activates when POLYGON_API_KEY is set.
Untested against the live API in this build (no key available); wired against
Polygon's documented /v2/aggs/ticker/{ticker}/range endpoint response shape."""

from datetime import UTC, date, datetime

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.market_data.base import MarketDataProvider, OhlcvBar
from app.utils.exceptions import ExternalServiceError

logger = get_logger(__name__)

BASE_URL = "https://api.polygon.io"


class PolygonProvider(MarketDataProvider):
    name = "polygon"

    def is_configured(self) -> bool:
        return bool(settings.POLYGON_API_KEY)

    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> list[OhlcvBar]:
        if not self.is_configured():
            raise ExternalServiceError("Polygon is not configured — set POLYGON_API_KEY to enable this provider")

        url = f"{BASE_URL}/v2/aggs/ticker/{symbol}/range/1/day/{start.isoformat()}/{end.isoformat()}"
        params = {"adjusted": "true", "sort": "asc", "limit": 50000, "apiKey": settings.POLYGON_API_KEY}
        try:
            response = httpx.get(url, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Polygon request failed for {symbol}: {exc}") from exc

        results = payload.get("results")
        if not results:
            raise ExternalServiceError(f"Polygon returned no data for '{symbol}': {payload.get('status')}")

        bars: list[OhlcvBar] = []
        for bar in results:
            bar_date = datetime.fromtimestamp(bar["t"] / 1000, tz=UTC).date()
            bars.append(
                OhlcvBar(
                    date=bar_date,
                    open=float(bar["o"]),
                    high=float(bar["h"]),
                    low=float(bar["l"]),
                    close=float(bar["c"]),
                    adj_close=float(bar["c"]),
                    volume=float(bar["v"]),
                )
            )
        logger.info("polygon_fetch_success", symbol=symbol, bars=len(bars))
        return sorted(bars, key=lambda b: b.date)
