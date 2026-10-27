"""Parses a user-uploaded CSV into the normalized OHLCV shape.

Accepted column names are case-insensitive and tolerant of the two common
export formats: yfinance-style ("Adj Close") and generic OHLCV exports
(no adjusted close, in which case adj_close falls back to close).
"""

from datetime import date
from io import BytesIO

import pandas as pd

from app.market_data.base import MarketDataProvider, OhlcvBar
from app.utils.exceptions import ValidationFailedError

_COLUMN_ALIASES = {
    "date": "date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "adj close": "adj_close",
    "adj_close": "adj_close",
    "volume": "volume",
}

REQUIRED_COLUMNS = {"date", "open", "high", "low", "close", "volume"}


class CSVProvider(MarketDataProvider):
    name = "csv_upload"

    def is_configured(self) -> bool:
        return True

    def fetch_ohlcv(self, symbol: str, start: date, end: date) -> list[OhlcvBar]:
        raise NotImplementedError("CSVProvider is driven by parse_csv(), not fetch_ohlcv()")

    def parse_csv(self, file_bytes: bytes) -> list[OhlcvBar]:
        try:
            df = pd.read_csv(BytesIO(file_bytes))
        except Exception as exc:
            raise ValidationFailedError(f"Could not parse CSV file: {exc}") from exc

        df.columns = [c.strip().lower() for c in df.columns]
        df = df.rename(columns={k: v for k, v in _COLUMN_ALIASES.items() if k in df.columns})

        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValidationFailedError(
                f"CSV is missing required column(s): {', '.join(sorted(missing))}. "
                f"Expected at least: {', '.join(sorted(REQUIRED_COLUMNS))}"
            )

        if "adj_close" not in df.columns:
            df["adj_close"] = df["close"]

        bars: list[OhlcvBar] = []
        for _, row in df.iterrows():
            try:
                parsed_date = pd.Timestamp(row["date"]).date()
                bars.append(
                    OhlcvBar(
                        date=parsed_date,
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        adj_close=float(row["adj_close"]),
                        volume=float(row["volume"]),
                    )
                )
            except (ValueError, TypeError) as exc:
                raise ValidationFailedError(f"Invalid row in CSV: {row.to_dict()} ({exc})") from exc

        if not bars:
            raise ValidationFailedError("CSV file contained no data rows")

        return sorted(bars, key=lambda b: b.date)
