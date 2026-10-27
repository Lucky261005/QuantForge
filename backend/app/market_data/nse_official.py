"""NSE India official data provider — real implementation, no API key required (the
NSE website's own JSON API is public), activates immediately like the Yahoo Finance
provider. Untested against the live endpoint in this build (NSE aggressively blocks
requests without a real browser TLS fingerprint and session cookie from a residential
IP — the same class of network restriction documented for Yahoo Finance in this repo).

NSE's `www.nseindia.com` API rejects any request that doesn't first carry cookies
issued by visiting a normal page — a bare API call gets a 401/403. A working client
has to warm up a session against the homepage before calling the historical-data
endpoint, which is what `_warm_session` does here.
"""

from datetime import date, datetime

import httpx

from app.core.logging import get_logger
from app.market_data.base import MarketDataProvider, OhlcvBar
from app.utils.exceptions import ExternalServiceError

logger = get_logger(__name__)

BASE_URL = "https://www.nseindia.com"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


class NSEOfficialProvider(MarketDataProvider):
    name = "nse_official"

    def is_configured(self) -> bool:
        return True  # public API, no key required

    def _warm_session(self, client: httpx.Client) -> None:
        response = client.get(f"{BASE_URL}/get-quotes/equity", headers=_HEADERS, timeout=15)
        response.raise_for_status()

    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> list[OhlcvBar]:
        try:
            with httpx.Client(follow_redirects=True) as client:
                self._warm_session(client)
                url = f"{BASE_URL}/api/historical/cm/equity"
                params = {
                    "symbol": symbol,
                    "series": '["EQ"]',
                    "from": start.strftime("%d-%m-%Y"),
                    "to": end.strftime("%d-%m-%Y"),
                }
                response = client.get(url, headers=_HEADERS, params=params, timeout=30)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"NSE official request failed for {symbol}: {exc}") from exc

        rows = payload.get("data")
        if not rows:
            raise ExternalServiceError(f"NSE official returned no data for '{symbol}': {payload}")

        bars = [
            OhlcvBar(
                date=datetime.strptime(row["CH_TIMESTAMP"], "%Y-%m-%d").date(),
                open=float(row["CH_OPENING_PRICE"]),
                high=float(row["CH_TRADE_HIGH_PRICE"]),
                low=float(row["CH_TRADE_LOW_PRICE"]),
                close=float(row["CH_CLOSING_PRICE"]),
                adj_close=float(row["CH_CLOSING_PRICE"]),
                volume=float(row["CH_TOT_TRADED_QTY"]),
            )
            for row in rows
        ]
        logger.info("nse_official_fetch_success", symbol=symbol, bars=len(bars))
        return sorted(bars, key=lambda b: b.date)
