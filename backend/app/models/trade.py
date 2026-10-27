from datetime import date as date_type
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.backtest import Backtest


class TradeSide(StrEnum):
    LONG = "long"
    SHORT = "short"


class ExitReason(StrEnum):
    SIGNAL = "signal"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    END_OF_BACKTEST = "end_of_backtest"


class Trade(Base):
    """A single closed round-trip trade produced by a backtest run."""

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    backtest_id: Mapped[int] = mapped_column(ForeignKey("backtests.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False, index=True)

    side: Mapped[TradeSide] = mapped_column(Enum(TradeSide), nullable=False)
    entry_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    exit_price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    pnl: Mapped[float] = mapped_column(Float, nullable=False)
    pnl_pct: Mapped[float] = mapped_column(Float, nullable=False)
    exit_reason: Mapped[ExitReason] = mapped_column(Enum(ExitReason), nullable=False)

    backtest: Mapped["Backtest"] = relationship(back_populates="trades")
    asset: Mapped["Asset"] = relationship(back_populates="trades")
