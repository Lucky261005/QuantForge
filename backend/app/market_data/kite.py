"""Zerodha Kite Connect provider — real implementation, activates when both
KITE_API_KEY and KITE_ACCESS_TOKEN are set. Untested against the live API in this
build (no broker account available); wired against Kite Connect's documented
`/instruments` and `/instruments/historical/{instrument_token}/{interval}` shapes.

Kite's historical-data endpoint is keyed by numeric `instrument_token`, not the
trading symbol, so a real integration must first resolve the symbol against the
`/instruments` master list (a daily CSV dump of every tradable instrument) — unlike
Yahoo/Alpha Vantage/Polygon, which accept a ticker directly.
"""

import csv
import io
from datetime import date, datetime

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.market_data.base import MarketDataProvider, OhlcvBar
from app.utils.exceptions import ExternalServiceError

logger = get_logger(__name__)

BASE_URL = "https://api.kite.trade"


class KiteConnectProvider(MarketDataProvider):
    name = "kite_connect"

    def is_configured(self) -> bool:
        return bool(settings.KITE_API_KEY and settings.KITE_ACCESS_TOKEN)

    def _auth_headers(self) -> dict[str, str]:
        return {
            "X-Kite-Version": "3",
            "Authorization": f"token {settings.KITE_API_KEY}:{settings.KITE_ACCESS_TOKEN}",
        }

    def _resolve_instrument_token(self, client: httpx.Client, symbol: str, exchange: str = "NSE") -> int:
        response = client.get(f"{BASE_URL}/instruments/{exchange}", headers=self._auth_headers(), timeout=30)
        response.raise_for_status()
        reader = csv.DictReader(io.StringIO(response.text))
        for row in reader:
            if row["tradingsymbol"] == symbol:
                return int(row["instrument_token"])
        raise ExternalServiceError(f"Kite: no instrument found for '{symbol}' on {exchange}")

    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> list[OhlcvBar]:
        if not self.is_configured():
            raise ExternalServiceError(
                "Kite Connect is not configured — set KITE_API_KEY and KITE_ACCESS_TOKEN to enable this provider"
            )

        try:
            with httpx.Client() as client:
                instrument_token = self._resolve_instrument_token(client, symbol)
                url = f"{BASE_URL}/instruments/historical/{instrument_token}/day"
                params = {"from": start.isoformat(), "to": end.isoformat()}
                response = client.get(url, headers=self._auth_headers(), params=params, timeout=30)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Kite Connect request failed for {symbol}: {exc}") from exc

        candles = payload.get("data", {}).get("candles")
        if not candles:
            raise ExternalServiceError(f"Kite Connect returned no data for '{symbol}': {payload}")

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
        logger.info("kite_fetch_success", symbol=symbol, bars=len(bars))
        return sorted(bars, key=lambda b: b.date)
