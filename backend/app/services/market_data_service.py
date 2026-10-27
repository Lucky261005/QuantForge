"""Market data ingestion: download-and-cache from a provider, or CSV upload —
both paths converge on the same deduplicated storage."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.cache import get_cache
from app.core.logging import get_logger
from app.market_data.csv_provider import CSVProvider
from app.market_data.registry import get_provider
from app.models.asset import Asset, AssetType
from app.models.market_data import DataSource
from app.repositories.asset import AssetRepository, MarketDataRepository
from app.utils.exceptions import NotFoundError

logger = get_logger(__name__)


def _cache_key(symbol: str, start: date, end: date) -> str:
    return f"ohlcv:{symbol.upper()}:{start.isoformat()}:{end.isoformat()}"


def _bars_to_rows(asset_id: int, bars, source: DataSource) -> list[dict]:
    return [
        {
            "asset_id": asset_id,
            "date": bar.date,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "adj_close": bar.adj_close,
            "volume": bar.volume,
            "source": source,
        }
        for bar in bars
    ]


class MarketDataService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.assets = AssetRepository(db)
        self.market_data = MarketDataRepository(db)
        self.cache = get_cache()

    def _is_range_fully_cached(self, asset_id: int, start: date, end: date) -> bool:
        """Business rule for "prevent duplicate downloads": if every business day in
        the requested range already has a stored bar, skip the external API call."""
        existing = self.market_data.get_existing_dates(asset_id, start, end)
        expected_trading_days = sum(
            1 for i in range((end - start).days + 1) if (start + timedelta(days=i)).weekday() < 5
        )
        # Allow slack for exchange holidays: if we already have at least as many
        # bars as trading days minus a small holiday buffer, treat as cached.
        return expected_trading_days > 0 and len(existing) >= max(0, expected_trading_days - 15)

    def download(
        self,
        symbol: str,
        start: date,
        end: date,
        source: DataSource = DataSource.YAHOO_FINANCE,
        force_refresh: bool = False,
        overwrite: bool = True,
    ) -> tuple[Asset, int, bool]:
        """Returns (asset, bars_written, served_from_cache)."""
        asset = self.assets.get_or_create(symbol, asset_type=AssetType.EQUITY)
        self.assets.commit()

        if not force_refresh and self._is_range_fully_cached(asset.id, start, end):
            logger.info("market_data_cache_hit", symbol=symbol, start=start, end=end)
            return asset, 0, True

        provider = get_provider(source)
        bars = provider.fetch_ohlcv(symbol, start, end)
        rows = _bars_to_rows(asset.id, bars, source)
        written = self.market_data.bulk_upsert(rows, overwrite=overwrite)
        self.market_data.commit()
        # Any cached range of this symbol may overlap the new bars, not just this exact one.
        self.cache.invalidate_prefix(f"ohlcv:{symbol.upper()}:")
        logger.info("market_data_downloaded", symbol=symbol, bars=written, source=source.value)
        return asset, written, False

    def upload_csv(
        self,
        symbol: str,
        file_bytes: bytes,
        *,
        asset_type: AssetType = AssetType.EQUITY,
        exchange: str | None = None,
        sector: str | None = None,
        industry: str | None = None,
        market_cap_cr: float | None = None,
        overwrite: bool = True,
        synthetic: bool = False,
    ) -> tuple[Asset, int]:
        asset = self.assets.get_or_create(
            symbol,
            asset_type=asset_type,
            exchange=exchange,
            sector=sector,
            industry=industry,
            market_cap_cr=market_cap_cr,
        )
        metadata_changed = False
        for field, value in (
            ("exchange", exchange),
            ("sector", sector),
            ("industry", industry),
            ("market_cap_cr", market_cap_cr),
        ):
            current = getattr(asset, field)
            # Without overwrite, metadata can be filled in but never replaced.
            if value is not None and current != value and (overwrite or current is None):
                setattr(asset, field, value)
                metadata_changed = True
        self.assets.commit()
        if metadata_changed:
            logger.info("asset_metadata_updated", symbol=symbol)

        bars = CSVProvider().parse_csv(file_bytes)
        rows = _bars_to_rows(asset.id, bars, DataSource.SYNTHETIC if synthetic else DataSource.CSV_UPLOAD)
        written = self.market_data.bulk_upsert(rows, overwrite=overwrite)
        self.market_data.commit()
        if bars:
            # Any cached range of this symbol may overlap the new bars, not just this exact one.
            self.cache.invalidate_prefix(f"ohlcv:{symbol.upper()}:")
        logger.info("market_data_csv_uploaded", symbol=symbol, bars=written)
        return asset, written

    def get_ohlcv(self, symbol: str, start: date, end: date) -> list[dict]:
        asset = self.assets.get_by_symbol(symbol)
        if not asset:
            raise NotFoundError(f"No data on file for symbol '{symbol}'. Download it first.")

        key = _cache_key(symbol, start, end)
        cached = self.cache.get_json(key)
        if cached is not None:
            return cached

        rows = self.market_data.get_range(asset.id, start, end)
        data = [
            {
                "date": r.date.isoformat(),
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "adj_close": r.adj_close,
                "volume": r.volume,
            }
            for r in rows
        ]
        self.cache.set_json(key, data)
        return data

    def list_assets(self, offset: int, limit: int) -> tuple[list[Asset], int]:
        return self.assets.list(offset=offset, limit=limit), self.assets.count()

    def latest_bar_dates(self, asset_ids: list[int]) -> dict[int, date]:
        return self.market_data.latest_dates(asset_ids)

    def synthetic_asset_ids(self, asset_ids: list[int]) -> set[int]:
        return self.market_data.synthetic_asset_ids(asset_ids)

    def get_market_breadth(self) -> dict:
        """Advance/decline and 52-week-high/low counts across every stored equity —
        computed entirely from OHLCV already on file, no external data feed. One
        bulk query for the whole universe (`get_range_for_assets`) rather than one
        query per symbol, so this stays cheap as the equity universe grows."""
        equities = self.assets.list(offset=0, limit=1000, asset_type=AssetType.EQUITY)
        if not equities:
            return {
                "advancing": 0,
                "declining": 0,
                "unchanged": 0,
                "new_52w_highs": 0,
                "new_52w_lows": 0,
                "total": 0,
            }

        # Anchor to the newest stored bar, not today: stored history can end well before
        # today (e.g. a static demo dataset), and a today-based window would come up empty.
        latest = self.market_data.latest_dates([a.id for a in equities])
        if not latest:
            return {"advancing": 0, "declining": 0, "unchanged": 0, "new_52w_highs": 0, "new_52w_lows": 0, "total": 0}
        end = max(latest.values())
        start = end - timedelta(days=370)  # ~52 weeks of calendar days plus a small buffer
        bars = self.market_data.get_range_for_assets([a.id for a in equities], start, end)

        by_asset: dict[int, list] = {}
        for bar in bars:
            by_asset.setdefault(bar.asset_id, []).append(bar)

        advancing = declining = unchanged = new_highs = new_lows = 0
        for asset_bars in by_asset.values():
            if len(asset_bars) < 2:
                continue
            asset_bars.sort(key=lambda b: b.date)
            closes = [b.close for b in asset_bars]
            last, prev = closes[-1], closes[-2]
            if last > prev:
                advancing += 1
            elif last < prev:
                declining += 1
            else:
                unchanged += 1
            if last >= max(closes):
                new_highs += 1
            if last <= min(closes):
                new_lows += 1

        return {
            "advancing": advancing,
            "declining": declining,
            "unchanged": unchanged,
            "new_52w_highs": new_highs,
            "new_52w_lows": new_lows,
            "total": len(by_asset),
        }
