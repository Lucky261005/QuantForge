"""Alpha Vantage provider — real implementation, activates when ALPHA_VANTAGE_API_KEY
is set. Untested against the live API in this build (no key available); wired against
Alpha Vantage's documented TIME_SERIES_DAILY_ADJUSTED response shape."""

from datetime import date, datetime

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.market_data.base import MarketDataProvider, OhlcvBar
from app.utils.exceptions import ExternalServiceError

logger = get_logger(__name__)

BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantageProvider(MarketDataProvider):
    name = "alpha_vantage"

    def is_configured(self) -> bool:
        return bool(settings.ALPHA_VANTAGE_API_KEY)

    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> list[OhlcvBar]:
        if not self.is_configured():
            raise ExternalServiceError(
                "Alpha Vantage is not configured — set ALPHA_VANTAGE_API_KEY to enable this provider"
            )

        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": "full",
            "apikey": settings.ALPHA_VANTAGE_API_KEY,
        }
        try:
            response = httpx.get(BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Alpha Vantage request failed for {symbol}: {exc}") from exc

        series = payload.get("Time Series (Daily)")
        if not series:
            raise ExternalServiceError(
                f"Alpha Vantage returned no data for '{symbol}': {payload.get('Note') or payload.get('Error Message') or payload}"
            )

        bars: list[OhlcvBar] = []
        for date_str, values in series.items():
            bar_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if not (start <= bar_date <= end):
                continue
            bars.append(
                OhlcvBar(
                    date=bar_date,
                    open=float(values["1. open"]),
                    high=float(values["2. high"]),
                    low=float(values["3. low"]),
                    close=float(values["4. close"]),
                    adj_close=float(values["5. adjusted close"]),
                    volume=float(values["6. volume"]),
                )
            )
        logger.info("alpha_vantage_fetch_success", symbol=symbol, bars=len(bars))
        return sorted(bars, key=lambda b: b.date)
