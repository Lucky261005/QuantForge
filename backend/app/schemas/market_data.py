from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.asset import AssetType
from app.models.market_data import DataSource


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    name: str | None
    asset_type: AssetType
    exchange: str | None
    currency: str
    sector: str | None = None
    industry: str | None = None
    market_cap_cr: float | None = None
    # Date of the newest stored bar; lets clients anchor "recent" to the data, not today.
    latest_bar_date: date | None = None
    # True when any stored bar is generated demo data rather than real market data.
    is_synthetic: bool = False


class DownloadRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    start_date: date
    end_date: date
    source: DataSource = DataSource.YAHOO_FINANCE
    force_refresh: bool = False


class DownloadResponse(BaseModel):
    asset: AssetRead
    bars_written: int
    served_from_cache: bool


class UploadResponse(BaseModel):
    asset: AssetRead
    bars_written: int


class OhlcvBarRead(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: float


class OhlcvSeriesResponse(BaseModel):
    symbol: str
    bars: list[OhlcvBarRead]


class MarketBreadthResponse(BaseModel):
    advancing: int
    declining: int
    unchanged: int
    new_52w_highs: int
    new_52w_lows: int
    total: int
