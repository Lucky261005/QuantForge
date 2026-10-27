from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.backtesting.optimizer import OptimizationMethod


class OptimizeRequest(BaseModel):
    symbols: list[str] = Field(min_length=2, max_length=20)
    start_date: date
    end_date: date
    method: OptimizationMethod = OptimizationMethod.MAX_SHARPE
    risk_free_rate: float = 0.0

    @field_validator("symbols")
    @classmethod
    def uppercase(cls, v: list[str]) -> list[str]:
        return [s.upper() for s in v]


class OptimizeResponse(BaseModel):
    method: OptimizationMethod
    weights: dict[str, float]
    expected_return_pct: float
    expected_volatility_pct: float
    sharpe_ratio: float
