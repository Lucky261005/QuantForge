from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.market_data import AssetRead


class WatchlistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class WatchlistItemAdd(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)


class WatchlistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset: AssetRead
    added_at: datetime


class WatchlistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    items: list[WatchlistItemRead] = []
