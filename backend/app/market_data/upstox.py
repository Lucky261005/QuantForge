"""Upstox provider — real implementation, activates when UPSTOX_ACCESS_TOKEN is set.
Untested against the live API in this build (no broker account available); wired
against Upstox API v2's documented historical-candle endpoint shape.

Upstox keys instruments as `{exchange}_{segment}|{isin_or_symbol}` (an "instrument
key"), resolved in production against Upstox's published instrument master JSON/CSV.
Resolving that fully is out of scope for an interface-only stub, so this uses the
`NSE_EQ|{symbol}` convention Upstox documents for plain NSE equity symbols — correct
for most large-cap tickers, but not a substitute for the real instrument master for
ISIN-keyed lookups (F&O, corporate-action-renamed symbols, etc.).
"""

from datetime import date, datetime

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.market_data.base import MarketDataProvider, OhlcvBar
from app.utils.exceptions import ExternalServiceError

logger = get_logger(__name__)

BASE_URL = "https://api.upstox.com/v2"


class UpstoxProvider(MarketDataProvider):
    name = "upstox"

    def is_configured(self) -> bool:
        return bool(settings.UPSTOX_ACCESS_TOKEN)

    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> list[OhlcvBar]:
        if not self.is_configured():
            raise ExternalServiceError("Upstox is not configured — set UPSTOX_ACCESS_TOKEN to enable this provider")

        instrument_key = f"NSE_EQ|{symbol}"
        url = f"{BASE_URL}/historical-candle/{instrument_key}/day/{end.isoformat()}/{start.isoformat()}"
        headers = {
            "Authorization": f"Bearer {settings.UPSTOX_ACCESS_TOKEN}",
            "Accept": "application/json",
        }
        try:
            response = httpx.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Upstox request failed for {symbol}: {exc}") from exc

        candles = payload.get("data", {}).get("candles")
        if not candles:
            raise ExternalServiceError(f"Upstox returned no data for '{symbol}': {payload}")

        bars = [
            OhlcvBar(
                date=datetime.fromisoformat(candle[0]).date(),
                open=float(candle[1]),
                high=float(candle[2]),
                low=float(candle[3]),
                close=float(candle[4]),
                adj_close=float(candle[4]),
                volume=float(candle[5]),
            )
            for candle in candles
        ]
        logger.info("upstox_fetch_success", symbol=symbol, bars=len(bars))
        return sorted(bars, key=lambda b: b.date)
