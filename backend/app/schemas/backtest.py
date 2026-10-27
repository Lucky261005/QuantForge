from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.backtesting.charges import ChargeModel
from app.models.backtest import BacktestStatus


class BacktestCreate(BaseModel):
    strategy_id: int
    name: str | None = None
    symbols: list[str] = Field(min_length=1, max_length=20)
    start_date: date
    end_date: date
    initial_capital: float = Field(default=100_000.0, gt=0)
    commission_pct: float = Field(default=0.001, ge=0, le=0.1)
    slippage_pct: float = Field(default=0.0005, ge=0, le=0.1)
    position_size_pct: float = Field(default=1.0, gt=0, le=1.0)
    stop_loss_pct: float | None = Field(default=None, gt=0, le=1.0)
    take_profit_pct: float | None = Field(default=None, gt=0, le=5.0)
    benchmark_symbol: str = "NIFTY50"
    charge_model: ChargeModel = ChargeModel.FLAT
    brokerage_pct: float = Field(default=0.0, ge=0, le=0.1)
    # Annualized risk-free rate used in Sharpe/Sortino (e.g. 0.07 for a 7% T-bill
    # yield) — defaults to 0 rather than silently assuming a rate, since the two
    # produce meaningfully different Sharpe values and this should be an explicit choice.
    risk_free_rate_annual: float = Field(default=0.0, ge=0, le=0.25)
    # Only meaningful for multi-symbol backtests — periodically resets each symbol
    # back to equal weight instead of letting winners drift to a larger share.
    rebalance_frequency: Literal["none", "monthly", "quarterly"] = "none"

    @field_validator("symbols")
    @classmethod
    def uppercase_symbols(cls, v: list[str]) -> list[str]:
        return [s.upper() for s in v]

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start and v <= start:
            raise ValueError("end_date must be after start_date")
        return v


class BacktestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    strategy_id: int
    name: str | None
    symbols: list[str]
    start_date: date
    end_date: date
    initial_capital: float
    commission_pct: float
    slippage_pct: float
    position_size_pct: float
    stop_loss_pct: float | None
    take_profit_pct: float | None
    benchmark_symbol: str
    charge_model: ChargeModel
    brokerage_pct: float
    risk_free_rate_annual: float
    rebalance_frequency: Literal["none", "monthly", "quarterly"]
    status: BacktestStatus
    strategy_version_hash: str | None
    runtime_seconds: float | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class BacktestStatusRead(BaseModel):
    id: int
    status: BacktestStatus
    error_message: str | None
    runtime_seconds: float | None


class BacktestMetricsRead(BaseModel):
    total_return_pct: float
    cagr_pct: float
    volatility_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    omega_ratio: float
    max_drawdown_pct: float
    ulcer_index: float
    var_95_pct: float
    cvar_95_pct: float
    max_consecutive_losses: int
    recovery_days: int | None
    num_trades: int
    win_rate_pct: float
    profit_factor: float
    expectancy: float
    alpha: float
    beta: float
    sharpe_ratio_ci_low: float
    sharpe_ratio_ci_high: float
    cagr_pct_ci_low: float
    cagr_pct_ci_high: float


class BacktestEquityRead(BaseModel):
    equity_curve: list[dict[str, Any]]
    drawdown_curve: list[dict[str, Any]]
    monthly_returns: list[dict[str, Any]]
    daily_returns: list[dict[str, Any]]


class CompareRequest(BaseModel):
    backtest_ids: list[int] = Field(min_length=2, max_length=10)


class CompareEntry(BaseModel):
    backtest_id: int
    name: str | None
    strategy_type: str
    metrics: BacktestMetricsRead
    equity_curve: list[dict[str, Any]]


class CompareResponse(BaseModel):
    entries: list[CompareEntry]
    correlation_matrix: dict[str, dict[str, float]]


class CostSensitivityEntry(BaseModel):
    cost_multiplier: float
    effective_commission_pct: float
    effective_slippage_pct: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    num_trades: int


class WalkForwardWindow(BaseModel):
    window: int
    start_date: str
    end_date: str
    total_return_pct: float | None = None
    sharpe_ratio: float | None = None
    max_drawdown_pct: float | None = None
    num_trades: int | None = None
    error: str | None = None
