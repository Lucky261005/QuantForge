from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.watchlist import Watchlist, WatchlistItem
from app.repositories.base import BaseRepository


class WatchlistRepository(BaseRepository[Watchlist]):
    model = Watchlist

    def list_for_owner(self, owner_id: int) -> list[Watchlist]:
        # Eager-load items + each item's asset in two extra queries total (not one per
        # watchlist, one per item) — WatchlistRead serializes both relationships on
        # every list call, so without this every watchlist page load was N+1.
        stmt = (
            select(Watchlist)
            .where(Watchlist.owner_id == owner_id)
            .options(selectinload(Watchlist.items).selectinload(WatchlistItem.asset))
            .order_by(Watchlist.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_with_items(self, watchlist_id: int) -> Watchlist | None:
        stmt = (
            select(Watchlist)
            .where(Watchlist.id == watchlist_id)
            .options(selectinload(Watchlist.items).selectinload(WatchlistItem.asset))
        )
        return self.db.scalar(stmt)


class WatchlistItemRepository(BaseRepository[WatchlistItem]):
    model = WatchlistItem

    def get_by_watchlist_and_asset(self, watchlist_id: int, asset_id: int) -> WatchlistItem | None:
        stmt = select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist_id, WatchlistItem.asset_id == asset_id
        )
        return self.db.scalar(stmt)

    def list_for_watchlist(self, watchlist_id: int) -> list[WatchlistItem]:
        stmt = (
            select(WatchlistItem)
            .where(WatchlistItem.watchlist_id == watchlist_id)
            .options(selectinload(WatchlistItem.asset))
        )
        return list(self.db.scalars(stmt).all())
