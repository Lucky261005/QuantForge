from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.backtest import Backtest
from app.models.trade import Trade
from app.repositories.base import BaseRepository


class BacktestRepository(BaseRepository[Backtest]):
    model = Backtest

    def get_with_strategy(self, id_: int) -> Backtest | None:
        """Eager-loads `strategy` in the same query — use this instead of the bare
        `.get()` anywhere the caller touches `backtest.strategy` afterward (e.g.
        AnalyticsService.compare), otherwise each backtest costs an extra query."""
        stmt = select(Backtest).where(Backtest.id == id_).options(joinedload(Backtest.strategy))
        return self.db.scalar(stmt)

    def list_for_owner(self, owner_id: int, offset: int = 0, limit: int = 20) -> list[Backtest]:
        stmt = (
            select(Backtest)
            .where(Backtest.owner_id == owner_id)
            .order_by(Backtest.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def count_for_owner(self, owner_id: int) -> int:
        return self.count(owner_id=owner_id)


class TradeRepository(BaseRepository[Trade]):
    model = Trade

    def list_for_backtest(self, backtest_id: int) -> list[Trade]:
        stmt = select(Trade).where(Trade.backtest_id == backtest_id).order_by(Trade.entry_date.asc())
        return list(self.db.scalars(stmt).all())
