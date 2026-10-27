from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.market_data import MarketData
    from app.models.portfolio import PortfolioHolding, Transaction
    from app.models.trade import Trade
    from app.models.watchlist import WatchlistItem


class AssetType(StrEnum):
    EQUITY = "equity"
    ETF = "etf"
    CRYPTO = "crypto"
    FOREX = "forex"
    INDEX = "index"
    OTHER = "other"


class Asset(TimestampMixin, Base):
    __tablename__ = "assets"
    __table_args__ = (UniqueConstraint("symbol", name="uq_assets_symbol"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), default=AssetType.EQUITY, nullable=False)
    exchange: Mapped[str | None] = mapped_column(String(50), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Market cap in INR crore (1 crore = 10,000,000) — the unit Indian exchanges/providers report in.
    market_cap_cr: Mapped[float | None] = mapped_column(Float, nullable=True)

    market_data: Mapped[list["MarketData"]] = relationship(back_populates="asset", cascade="all, delete-orphan")
    trades: Mapped[list["Trade"]] = relationship(back_populates="asset")
    watchlist_items: Mapped[list["WatchlistItem"]] = relationship(back_populates="asset")
    portfolio_holdings: Mapped[list["PortfolioHolding"]] = relationship(back_populates="asset")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="asset")

    def __repr__(self) -> str:
        return f"<Asset {self.symbol}>"
