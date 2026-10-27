from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.market_data import MarketData
from app.models.portfolio import Portfolio, PortfolioHolding, Transaction, TransactionType
from app.repositories.asset import AssetRepository
from app.repositories.portfolio import PortfolioHoldingRepository, PortfolioRepository, TransactionRepository
from app.utils.exceptions import NotFoundError, ValidationFailedError


class PortfolioService:
    """A simulated (paper-trading) portfolio for tracking research-driven positions —
    not connected to a real broker. Prices default to the latest stored close for the
    asset unless an explicit price is supplied."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.portfolios = PortfolioRepository(db)
        self.holdings = PortfolioHoldingRepository(db)
        self.transactions = TransactionRepository(db)
        self.assets = AssetRepository(db)

    def get_or_create(self, owner_id: int) -> Portfolio:
        portfolio = self.portfolios.get_by_owner(owner_id)
        if not portfolio:
            portfolio = self.portfolios.create(Portfolio(owner_id=owner_id))
            self.portfolios.commit()
        return portfolio

    def _latest_price(self, asset: Asset) -> float:
        stmt = select(MarketData).where(MarketData.asset_id == asset.id).order_by(MarketData.date.desc())
        row = self.db.scalar(stmt)
        if not row:
            raise ValidationFailedError(
                f"No market data on file for '{asset.symbol}'; download it first or supply an explicit price."
            )
        return row.close

    def deposit(self, owner_id: int, amount: float) -> Portfolio:
        if amount <= 0:
            raise ValidationFailedError("Deposit amount must be positive")
        portfolio = self.get_or_create(owner_id)
        portfolio.cash_balance += amount
        self.transactions.create(Transaction(portfolio_id=portfolio.id, type=TransactionType.DEPOSIT, amount=amount))
        self.db.commit()
        return portfolio

    def withdraw(self, owner_id: int, amount: float) -> Portfolio:
        portfolio = self.get_or_create(owner_id)
        if amount <= 0 or amount > portfolio.cash_balance:
            raise ValidationFailedError("Withdrawal amount must be positive and not exceed the cash balance")
        portfolio.cash_balance -= amount
        self.transactions.create(Transaction(portfolio_id=portfolio.id, type=TransactionType.WITHDRAW, amount=amount))
        self.db.commit()
        return portfolio

    def buy(self, owner_id: int, symbol: str, quantity: float, price: float | None = None) -> Portfolio:
        if quantity <= 0:
            raise ValidationFailedError("Quantity must be positive")
        portfolio = self.get_or_create(owner_id)
        asset = self.assets.get_or_create(symbol)
        self.assets.commit()
        trade_price = price if price is not None else self._latest_price(asset)
        cost = quantity * trade_price
        if cost > portfolio.cash_balance:
            raise ValidationFailedError("Insufficient cash balance for this purchase")

        portfolio.cash_balance -= cost
        holding = self.holdings.get_by_portfolio_and_asset(portfolio.id, asset.id)
        if holding:
            new_qty = holding.quantity + quantity
            holding.avg_price = (holding.avg_price * holding.quantity + trade_price * quantity) / new_qty
            holding.quantity = new_qty
        else:
            self.holdings.create(
                PortfolioHolding(portfolio_id=portfolio.id, asset_id=asset.id, quantity=quantity, avg_price=trade_price)
            )

        self.transactions.create(
            Transaction(
                portfolio_id=portfolio.id,
                asset_id=asset.id,
                type=TransactionType.BUY,
                quantity=quantity,
                price=trade_price,
                amount=cost,
            )
        )
        self.db.commit()
        return portfolio

    def sell(self, owner_id: int, symbol: str, quantity: float, price: float | None = None) -> Portfolio:
        if quantity <= 0:
            raise ValidationFailedError("Quantity must be positive")
        portfolio = self.get_or_create(owner_id)
        asset = self.assets.get_by_symbol(symbol)
        if not asset:
            raise NotFoundError(f"No asset on file for symbol '{symbol}'")

        holding = self.holdings.get_by_portfolio_and_asset(portfolio.id, asset.id)
        if not holding or holding.quantity < quantity:
            raise ValidationFailedError(f"Insufficient shares of '{symbol}' to sell")

        trade_price = price if price is not None else self._latest_price(asset)
        proceeds = quantity * trade_price
        holding.quantity -= quantity
        portfolio.cash_balance += proceeds
        if holding.quantity == 0:
            self.holdings.delete(holding)

        self.transactions.create(
            Transaction(
                portfolio_id=portfolio.id,
                asset_id=asset.id,
                type=TransactionType.SELL,
                quantity=quantity,
                price=trade_price,
                amount=proceeds,
            )
        )
        self.db.commit()
        return portfolio

    def list_transactions(self, owner_id: int, offset: int, limit: int):
        portfolio = self.get_or_create(owner_id)
        return (
            self.transactions.list_for_portfolio(portfolio.id, offset, limit),
            self.transactions.count_for_portfolio(portfolio.id),
        )
