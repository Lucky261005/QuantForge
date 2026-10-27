from datetime import date as date_type
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Date, DateTime, Enum, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.backtesting.charges import ChargeModel
from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.strategy import Strategy
    from app.models.trade import Trade
    from app.models.user import User


class BacktestStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Backtest(TimestampMixin, Base):
    """A single backtest run. Carries experiment-tracking metadata so results stay
    reproducible even after the parent strategy's parameters are later edited."""

    __tablename__ = "backtests"
    __table_args__ = (Index("ix_backtests_owner_id_status", "owner_id", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy_id: Mapped[int] = mapped_column(
        ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # Backtest configuration
    symbols: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    start_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    end_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    initial_capital: Mapped[float] = mapped_column(Float, nullable=False, default=100_000.0)
    commission_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.001)
    slippage_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0005)
    position_size_pct: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    stop_loss_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    benchmark_symbol: Mapped[str] = mapped_column(String(20), nullable=False, default="NIFTY50")
    # Indian cash-equity charge model — statutory charges (STT/exchange/SEBI/stamp duty/GST)
    # are computed from fixed regulator-set rates in app/backtesting/charges.py; only
    # brokerage is user-configurable. CHARGE_MODEL.FLAT (default) preserves the original
    # blended commission_pct/slippage_pct model unchanged.
    charge_model: Mapped[ChargeModel] = mapped_column(Enum(ChargeModel), default=ChargeModel.FLAT, nullable=False)
    brokerage_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_free_rate_annual: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rebalance_frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="none")

    # Execution / experiment tracking
    status: Mapped[BacktestStatus] = mapped_column(
        Enum(BacktestStatus), default=BacktestStatus.PENDING, nullable=False, index=True
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    strategy_version_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parameters_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    runtime_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="backtests")
    strategy: Mapped["Strategy"] = relationship(back_populates="backtests")
    trades: Mapped[list["Trade"]] = relationship(back_populates="backtest", cascade="all, delete-orphan")
    result: Mapped["BacktestResult | None"] = relationship(
        back_populates="backtest", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Backtest id={self.id} status={self.status}>"


class BacktestResult(Base):
    """1:1 with Backtest. All heavy analytics precomputed once when the run completes."""

    __tablename__ = "backtest_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    backtest_id: Mapped[int] = mapped_column(
        ForeignKey("backtests.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Returns
    total_return_pct: Mapped[float] = mapped_column(Float, nullable=False)
    cagr_pct: Mapped[float] = mapped_column(Float, nullable=False)
    volatility_pct: Mapped[float] = mapped_column(Float, nullable=False)

    # Risk-adjusted
    sharpe_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    sortino_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    calmar_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    omega_ratio: Mapped[float] = mapped_column(Float, nullable=False)

    # Drawdown / tail risk
    max_drawdown_pct: Mapped[float] = mapped_column(Float, nullable=False)
    ulcer_index: Mapped[float] = mapped_column(Float, nullable=False)
    var_95_pct: Mapped[float] = mapped_column(Float, nullable=False)
    cvar_95_pct: Mapped[float] = mapped_column(Float, nullable=False)
    max_consecutive_losses: Mapped[int] = mapped_column(Integer, nullable=False)
    recovery_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Trade stats
    num_trades: Mapped[int] = mapped_column(Integer, nullable=False)
    win_rate_pct: Mapped[float] = mapped_column(Float, nullable=False)
    profit_factor: Mapped[float] = mapped_column(Float, nullable=False)
    expectancy: Mapped[float] = mapped_column(Float, nullable=False)

    # Relative to benchmark
    alpha: Mapped[float] = mapped_column(Float, nullable=False)
    beta: Mapped[float] = mapped_column(Float, nullable=False)

    # Block-bootstrap 95% confidence intervals (see backtesting/metrics.py) — a point
    # Sharpe/CAGR estimate alone overstates how much a few hundred daily returns can
    # actually support statistically.
    sharpe_ratio_ci_low: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sharpe_ratio_ci_high: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cagr_pct_ci_low: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cagr_pct_ci_high: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Time series payloads (JSON) for charting
    equity_curve: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    drawdown_curve: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    monthly_returns: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    daily_returns: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)

    backtest: Mapped["Backtest"] = relationship(back_populates="result")
