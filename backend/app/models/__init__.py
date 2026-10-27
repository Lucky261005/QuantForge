"""Import every model here so Alembic's autogenerate and Base.metadata see them all."""

from app.db.base_class import Base
from app.models.asset import Asset
from app.models.audit_log import AuditLog
from app.models.backtest import Backtest, BacktestResult
from app.models.market_data import MarketData
from app.models.portfolio import Portfolio, PortfolioHolding, Transaction
from app.models.refresh_token import RefreshToken
from app.models.research_note import ResearchNote
from app.models.strategy import Strategy
from app.models.trade import Trade
from app.models.user import User
from app.models.watchlist import Watchlist, WatchlistItem

__all__ = [
    "Base",
    "User",
    "RefreshToken",
    "Asset",
    "MarketData",
    "Strategy",
    "Backtest",
    "BacktestResult",
    "Trade",
    "Watchlist",
    "WatchlistItem",
    "ResearchNote",
    "Portfolio",
    "PortfolioHolding",
    "Transaction",
    "AuditLog",
]
