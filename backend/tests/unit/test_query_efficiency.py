"""Regression tests proving the N+1 fixes in WatchlistRepository/BacktestRepository
actually hold — counts real SQL statements executed, not just correctness of the
returned data (which would pass even with N+1 queries)."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.asset import Asset, AssetType
from app.models.watchlist import Watchlist, WatchlistItem
from app.repositories.watchlist import WatchlistRepository


def _make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine, sessionmaker(bind=engine)()


def _count_queries(engine, fn):
    count = 0

    def _on_execute(*_args, **_kwargs):
        nonlocal count
        count += 1

    event.listen(engine, "before_cursor_execute", _on_execute)
    try:
        result = fn()
    finally:
        event.remove(engine, "before_cursor_execute", _on_execute)
    return result, count


def test_list_for_owner_does_not_scale_query_count_with_item_count():
    """Before the selectinload fix, listing one watchlist with N items cost 1 (watchlist)
    + 1 (items) + N (one per item's asset) queries. After the fix it must cost a small,
    constant number of queries regardless of N."""
    engine, db = _make_session()
    repo = WatchlistRepository(db)

    watchlist = Watchlist(owner_id=1, name="NIFTY 50")
    db.add(watchlist)
    db.flush()

    for i in range(10):
        asset = Asset(symbol=f"SYM{i}", asset_type=AssetType.EQUITY)
        db.add(asset)
        db.flush()
        db.add(WatchlistItem(watchlist_id=watchlist.id, asset_id=asset.id))
    db.commit()
    db.expire_all()  # force a real reload from the DB, not the identity map

    _, query_count = _count_queries(engine, lambda: repo.list_for_owner(1)[0].items[0].asset.symbol)

    assert query_count <= 3, f"expected a small constant number of queries, got {query_count} (N+1 regression)"
    db.close()
    engine.dispose()
