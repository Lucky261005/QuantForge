from datetime import date

import pandas as pd
import yfinance as yf
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.logging import get_logger
from app.market_data.base import MarketDataProvider, OhlcvBar
from app.utils.exceptions import ExternalServiceError

logger = get_logger(__name__)


def _to_yahoo_symbol(symbol: str) -> str:
    """Yahoo Finance requires NSE/BSE tickers to carry an exchange suffix
    (`RELIANCE.NS`, `RELIANCE.BO`) — plain symbols are assumed to be NSE-listed,
    since that's this platform's default market. Already-suffixed symbols (`.NS`,
    `.BO`) and index tickers (`^NSEI`, `^BSESN`) pass through unchanged."""
    if "." in symbol or symbol.startswith("^"):
        return symbol
    return f"{symbol}.NS"


class YahooFinanceProvider(MarketDataProvider):
    name = "yahoo_finance"

    def is_configured(self) -> bool:
        return True  # No API key required.

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(ExternalServiceError),
        reraise=True,
    )
    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> list[OhlcvBar]:
        yahoo_symbol = _to_yahoo_symbol(symbol)
        try:
            df: pd.DataFrame = yf.download(
                yahoo_symbol,
                start=start.isoformat(),
                end=end.isoformat(),
                progress=False,
                auto_adjust=False,
                multi_level_index=False,
            )
        except Exception as exc:  # yfinance raises assorted network/HTTP errors
            raise ExternalServiceError(f"Yahoo Finance request failed for {yahoo_symbol}: {exc}") from exc

        if df is None or df.empty:
            raise ExternalServiceError(f"Yahoo Finance returned no data for symbol '{yahoo_symbol}'")

        df = df.reset_index()
        bars: list[OhlcvBar] = []
        for _, row in df.iterrows():
            bars.append(
                OhlcvBar(
                    date=pd.Timestamp(row["Date"]).date(),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    adj_close=float(row.get("Adj Close", row["Close"])),
                    volume=float(row["Volume"]),
                )
            )
        logger.info("yahoo_fetch_success", symbol=symbol, bars=len(bars))
        return bars
