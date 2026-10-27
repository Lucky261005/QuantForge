"""Angel One SmartAPI provider — real implementation, activates when
ANGEL_ONE_API_KEY, ANGEL_ONE_JWT_TOKEN, and ANGEL_ONE_CLIENT_CODE are all set.
Untested against the live API in this build (no broker account available); wired
against SmartAPI's documented `getCandleData` endpoint shape.

SmartAPI keys historical requests by `symboltoken` (a numeric instrument id), which
in production is resolved against Angel One's published instrument master JSON —
out of scope for an interface-only stub, so this expects the caller to already know
the token (or extend `_resolve_symbol_token` once the master list is wired in).
"""

from datetime import date, datetime

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.market_data.base import MarketDataProvider, OhlcvBar
from app.utils.exceptions import ExternalServiceError

logger = get_logger(__name__)

BASE_URL = "https://apiconnect.angelbroking.com"


class AngelOneProvider(MarketDataProvider):
    name = "angel_one"

    def is_configured(self) -> bool:
        return bool(settings.ANGEL_ONE_API_KEY and settings.ANGEL_ONE_JWT_TOKEN and settings.ANGEL_ONE_CLIENT_CODE)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.ANGEL_ONE_JWT_TOKEN}",
            "X-PrivateKey": settings.ANGEL_ONE_API_KEY or "",
            "X-ClientLocalIP": "CLIENT_LOCAL_IP",
            "X-ClientPublicIP": "CLIENT_PUBLIC_IP",
            "X-MACAddress": "MAC_ADDRESS",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "Content-Type": "application/json",
        }

    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> list[OhlcvBar]:
        if not self.is_configured():
            raise ExternalServiceError(
                "Angel One is not configured — set ANGEL_ONE_API_KEY, ANGEL_ONE_JWT_TOKEN, and "
                "ANGEL_ONE_CLIENT_CODE to enable this provider"
            )

        url = f"{BASE_URL}/rest/secure/angelbroking/historical/v1/getCandleData"
        body = {
            "exchange": "NSE",
            "symboltoken": symbol,  # production integration must resolve the real symboltoken first
            "interval": "ONE_DAY",
            "fromdate": f"{start.isoformat()} 09:15",
            "todate": f"{end.isoformat()} 15:30",
        }
        try:
            response = httpx.post(url, json=body, headers=self._headers(), timeout=30)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Angel One request failed for {symbol}: {exc}") from exc

        candles = payload.get("data")
        if not candles:
            raise ExternalServiceError(f"Angel One returned no data for '{symbol}': {payload.get('message')}")

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
        logger.info("angel_one_fetch_success", symbol=symbol, bars=len(bars))
        return sorted(bars, key=lambda b: b.date)
