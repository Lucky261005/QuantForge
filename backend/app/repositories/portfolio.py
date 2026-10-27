from sqlalchemy import select

from app.models.portfolio import Portfolio, PortfolioHolding, Transaction
from app.repositories.base import BaseRepository


class PortfolioRepository(BaseRepository[Portfolio]):
    model = Portfolio

    def get_by_owner(self, owner_id: int) -> Portfolio | None:
        return self.db.scalar(select(Portfolio).where(Portfolio.owner_id == owner_id))


class PortfolioHoldingRepository(BaseRepository[PortfolioHolding]):
    model = PortfolioHolding

    def get_by_portfolio_and_asset(self, portfolio_id: int, asset_id: int) -> PortfolioHolding | None:
        stmt = select(PortfolioHolding).where(
            PortfolioHolding.portfolio_id == portfolio_id, PortfolioHolding.asset_id == asset_id
        )
        return self.db.scalar(stmt)

    def list_for_portfolio(self, portfolio_id: int) -> list[PortfolioHolding]:
        stmt = select(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio_id)
        return list(self.db.scalars(stmt).all())


class TransactionRepository(BaseRepository[Transaction]):
    model = Transaction

    def list_for_portfolio(self, portfolio_id: int, offset: int = 0, limit: int = 50) -> list[Transaction]:
        stmt = (
            select(Transaction)
            .where(Transaction.portfolio_id == portfolio_id)
            .order_by(Transaction.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def count_for_portfolio(self, portfolio_id: int) -> int:
        return self.count(portfolio_id=portfolio_id)
