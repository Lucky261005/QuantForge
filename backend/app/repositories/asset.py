from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.market_data import DataSource, MarketData
from app.repositories.base import BaseRepository


def _insert_for_dialect(db: Session):
    """Both SQLite and Postgres support `INSERT ... ON CONFLICT`, but the `insert()`
    builder that exposes `.excluded` and `.on_conflict_do_update` is dialect-specific."""
    if db.bind.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as dialect_insert
    else:
        from sqlalchemy.dialects.sqlite import insert as dialect_insert
    return dialect_insert


class AssetRepository(BaseRepository[Asset]):
    model = Asset

    def get_by_symbol(self, symbol: str) -> Asset | None:
        return self.db.scalar(select(Asset).where(Asset.symbol == symbol.upper()))

    def get_or_create(self, symbol: str, **defaults: object) -> Asset:
        asset = self.get_by_symbol(symbol)
        if asset:
            return asset
        asset = Asset(symbol=symbol.upper(), **defaults)
        return self.create(asset)


class MarketDataRepository:
    """Not a BaseRepository subclass: market data is bulk-upserted, not CRUD'd one row
    at a time, so it needs its own persistence shape."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_existing_dates(self, asset_id: int, start: date, end: date) -> set[date]:
        stmt = select(MarketData.date).where(
            MarketData.asset_id == asset_id, MarketData.date >= start, MarketData.date <= end
        )
        return set(self.db.scalars(stmt).all())

    def bulk_upsert(self, rows: list[dict], *, overwrite: bool = True) -> int:
        """Insert new (asset_id, date) bars. With `overwrite`, existing bars get their
        OHLCV values updated (e.g. a previously-partial day's adjusted close corrected);
        without it, existing bars are left untouched. Market data is shared by every
        user, so only admins write with overwrite. Returns the number of bars written."""
        if not rows:
            return 0
        dialect_insert = _insert_for_dialect(self.db)
        stmt = dialect_insert(MarketData).values(rows)
        if overwrite:
            update_cols = {
                c: stmt.excluded[c] for c in ("open", "high", "low", "close", "adj_close", "volume", "source")
            }
            stmt = stmt.on_conflict_do_update(index_elements=["asset_id", "date"], set_=update_cols)
            self.db.execute(stmt)
            self.db.flush()
            return len(rows)
        result = self.db.execute(stmt.on_conflict_do_nothing(index_elements=["asset_id", "date"]))
        self.db.flush()
        return result.rowcount

    def latest_dates(self, asset_ids: list[int]) -> dict[int, date]:
        """Newest stored bar date per asset, in one grouped query."""
        if not asset_ids:
            return {}
        stmt = (
            select(MarketData.asset_id, func.max(MarketData.date))
            .where(MarketData.asset_id.in_(asset_ids))
            .group_by(MarketData.asset_id)
        )
        return {asset_id: latest for asset_id, latest in self.db.execute(stmt).all()}

    def synthetic_asset_ids(self, asset_ids: list[int]) -> set[int]:
        """Assets with at least one generated (synthetic) bar."""
        if not asset_ids:
            return set()
        stmt = (
            select(MarketData.asset_id)
            .where(MarketData.asset_id.in_(asset_ids), MarketData.source == DataSource.SYNTHETIC)
            .distinct()
        )
        return set(self.db.scalars(stmt).all())

    def get_range(self, asset_id: int, start: date, end: date) -> list[MarketData]:
        stmt = (
            select(MarketData)
            .where(MarketData.asset_id == asset_id, MarketData.date >= start, MarketData.date <= end)
            .order_by(MarketData.date.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_range_for_assets(self, asset_ids: list[int], start: date, end: date) -> list[MarketData]:
        """Bulk variant of `get_range` — one query for every asset via `IN (...)`
        instead of one query per asset, for market-breadth-style aggregates that
        need recent bars across an entire universe of symbols at once."""
        if not asset_ids:
            return []
        stmt = (
            select(MarketData)
            .where(MarketData.asset_id.in_(asset_ids), MarketData.date >= start, MarketData.date <= end)
            .order_by(MarketData.asset_id.asc(), MarketData.date.asc())
        )
        return list(self.db.scalars(stmt).all())

    def commit(self) -> None:
        self.db.commit()
