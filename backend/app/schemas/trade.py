from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.trade import ExitReason, TradeSide


class TradeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    side: TradeSide
    entry_date: date
    entry_price: float
    exit_date: date
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    exit_reason: ExitReason
