from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.portfolio import TransactionType


class PortfolioHoldingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    quantity: float
    avg_price: float


class PortfolioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    cash_balance: float
    holdings: list[PortfolioHoldingRead] = []


class TransactionCreate(BaseModel):
    type: TransactionType
    symbol: str | None = Field(default=None, min_length=1, max_length=20)
    quantity: float = Field(default=0, ge=0)
    price: float = Field(default=0, ge=0)
    amount: float | None = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int | None
    type: TransactionType
    quantity: float
    price: float
    amount: float
    timestamp: datetime
