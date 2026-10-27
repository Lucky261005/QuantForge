from sqlalchemy.orm import Session

from app.models.user import User
from app.models.watchlist import Watchlist, WatchlistItem
from app.repositories.asset import AssetRepository
from app.repositories.watchlist import WatchlistItemRepository, WatchlistRepository
from app.utils.exceptions import AlreadyExistsError, NotFoundError, PermissionDeniedError


class WatchlistService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.watchlists = WatchlistRepository(db)
        self.items = WatchlistItemRepository(db)
        self.assets = AssetRepository(db)

    def create(self, owner_id: int, name: str) -> Watchlist:
        watchlist = self.watchlists.create(Watchlist(owner_id=owner_id, name=name))
        self.watchlists.commit()
        return watchlist

    def list_for_owner(self, owner_id: int) -> list[Watchlist]:
        return self.watchlists.list_for_owner(owner_id)

    def get_owned(self, watchlist_id: int, user: User) -> Watchlist:
        watchlist = self.watchlists.get(watchlist_id)
        if not watchlist:
            raise NotFoundError("Watchlist not found")
        if watchlist.owner_id != user.id:
            raise PermissionDeniedError("You do not have access to this watchlist")
        return watchlist

    def get_owned_with_items(self, watchlist_id: int, user: User) -> Watchlist:
        """Same ownership check as `get_owned`, but eager-loads items + each item's
        asset in two extra queries total — use this instead of `get_owned` whenever
        the result will be serialized through `WatchlistRead` (which touches both
        relationships), to avoid an N+1 query per item."""
        watchlist = self.watchlists.get_with_items(watchlist_id)
        if not watchlist:
            raise NotFoundError("Watchlist not found")
        if watchlist.owner_id != user.id:
            raise PermissionDeniedError("You do not have access to this watchlist")
        return watchlist

    def add_item(self, watchlist_id: int, user: User, symbol: str) -> WatchlistItem:
        watchlist = self.get_owned(watchlist_id, user)
        asset = self.assets.get_or_create(symbol)
        self.assets.commit()

        existing = self.items.get_by_watchlist_and_asset(watchlist.id, asset.id)
        if existing:
            raise AlreadyExistsError(f"{symbol} is already in this watchlist")

        item = self.items.create(WatchlistItem(watchlist_id=watchlist.id, asset_id=asset.id))
        self.items.commit()
        return item

    def remove_item(self, watchlist_id: int, item_id: int, user: User) -> None:
        watchlist = self.get_owned(watchlist_id, user)
        item = self.items.get(item_id)
        if not item or item.watchlist_id != watchlist.id:
            raise NotFoundError("Watchlist item not found")
        self.items.delete(item)
        self.items.commit()

    def delete(self, watchlist_id: int, user: User) -> None:
        watchlist = self.get_owned(watchlist_id, user)
        self.watchlists.delete(watchlist)
        self.watchlists.commit()
