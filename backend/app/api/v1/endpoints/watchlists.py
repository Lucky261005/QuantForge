from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import Message
from app.schemas.watchlist import WatchlistCreate, WatchlistItemAdd, WatchlistItemRead, WatchlistRead
from app.services.watchlist_service import WatchlistService

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


@router.post("", response_model=WatchlistRead, status_code=201)
def create_watchlist(payload: WatchlistCreate, user: CurrentUser, db: DbSession) -> WatchlistRead:
    watchlist = WatchlistService(db).create(user.id, payload.name)
    return WatchlistRead.model_validate(watchlist)


@router.get("", response_model=list[WatchlistRead])
def list_watchlists(user: CurrentUser, db: DbSession) -> list[WatchlistRead]:
    watchlists = WatchlistService(db).list_for_owner(user.id)
    return [WatchlistRead.model_validate(w) for w in watchlists]


@router.get("/{watchlist_id}", response_model=WatchlistRead)
def get_watchlist(watchlist_id: int, user: CurrentUser, db: DbSession) -> WatchlistRead:
    watchlist = WatchlistService(db).get_owned_with_items(watchlist_id, user)
    return WatchlistRead.model_validate(watchlist)


@router.post("/{watchlist_id}/items", response_model=WatchlistItemRead, status_code=201)
def add_item(watchlist_id: int, payload: WatchlistItemAdd, user: CurrentUser, db: DbSession) -> WatchlistItemRead:
    item = WatchlistService(db).add_item(watchlist_id, user, payload.symbol.upper())
    return WatchlistItemRead.model_validate(item)


@router.delete("/{watchlist_id}/items/{item_id}", response_model=Message)
def remove_item(watchlist_id: int, item_id: int, user: CurrentUser, db: DbSession) -> Message:
    WatchlistService(db).remove_item(watchlist_id, item_id, user)
    return Message(message="Item removed from watchlist")


@router.delete("/{watchlist_id}", response_model=Message)
def delete_watchlist(watchlist_id: int, user: CurrentUser, db: DbSession) -> Message:
    WatchlistService(db).delete(watchlist_id, user)
    return Message(message="Watchlist deleted")
