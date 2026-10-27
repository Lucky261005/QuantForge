from datetime import date as date_type
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.asset import Asset


class DataSource(StrEnum):
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"
    CSV_UPLOAD = "csv_upload"
    NSE_OFFICIAL = "nse_official"
    KITE_CONNECT = "kite_connect"
    UPSTOX = "upstox"
    ANGEL_ONE = "angel_one"
    SYNTHETIC = "synthetic"  # generated demo prices (scripts/seed_demo_data.py), not market data


class MarketData(Base):
    """One OHLCV bar. Unique on (asset_id, date) so re-downloading a range never duplicates rows."""

    __tablename__ = "market_data"
    __table_args__ = (UniqueConstraint("asset_id", "date", name="uq_market_data_asset_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    adj_close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    source: Mapped[DataSource] = mapped_column(Enum(DataSource), nullable=False)

    asset: Mapped["Asset"] = relationship(back_populates="market_data")
