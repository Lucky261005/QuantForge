from datetime import date
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import CurrentUser, DbSession, PageNumber, PageSize
from app.core.config import settings
from app.models.asset import AssetType
from app.models.user import UserRole
from app.schemas.common import Page
from app.schemas.market_data import (
    AssetRead,
    DownloadRequest,
    DownloadResponse,
    MarketBreadthResponse,
    OhlcvSeriesResponse,
    UploadResponse,
)
from app.services.market_data_service import MarketDataService

router = APIRouter(prefix="/assets", tags=["market-data"])
limiter = Limiter(key_func=get_remote_address)


@router.get("", response_model=Page[AssetRead])
def list_assets(user: CurrentUser, db: DbSession, page: PageNumber = 1, page_size: PageSize = 20) -> Page[AssetRead]:
    service = MarketDataService(db)
    items, total = service.list_assets(offset=(page - 1) * page_size, limit=page_size)
    ids = [a.id for a in items]
    latest = service.latest_bar_dates(ids)
    synthetic = service.synthetic_asset_ids(ids)
    reads = [
        AssetRead.model_validate(a).model_copy(
            update={"latest_bar_date": latest.get(a.id), "is_synthetic": a.id in synthetic}
        )
        for a in items
    ]
    return Page.create(reads, total, page, page_size)


@router.get("/breadth", response_model=MarketBreadthResponse)
def get_market_breadth(user: CurrentUser, db: DbSession) -> MarketBreadthResponse:
    """Advance/decline and 52-week high/low counts across every stored equity —
    computed from OHLCV already on file, no external market-breadth feed needed."""
    return MarketBreadthResponse(**MarketDataService(db).get_market_breadth())


@router.post("/download", response_model=DownloadResponse)
@limiter.limit(settings.RATE_LIMIT_DATA_DOWNLOAD)
def download_asset(request: Request, payload: DownloadRequest, user: CurrentUser, db: DbSession) -> DownloadResponse:
    service = MarketDataService(db)
    asset, written, cached = service.download(
        symbol=payload.symbol.upper(),
        start=payload.start_date,
        end=payload.end_date,
        source=payload.source,
        force_refresh=payload.force_refresh,
        overwrite=user.role == UserRole.ADMIN,  # shared data: only admins may replace existing bars
    )
    return DownloadResponse(asset=AssetRead.model_validate(asset), bars_written=written, served_from_cache=cached)


@router.post("/upload", response_model=UploadResponse)
@limiter.limit(settings.RATE_LIMIT_DATA_DOWNLOAD)
def upload_csv(
    request: Request,
    user: CurrentUser,
    db: DbSession,
    symbol: Annotated[str, Query(min_length=1, max_length=20)],
    asset_type: AssetType = AssetType.EQUITY,
    exchange: str | None = None,
    sector: str | None = None,
    industry: str | None = None,
    market_cap_cr: float | None = None,
    synthetic: bool = False,  # generated demo prices; labelled as such everywhere they appear
    file: UploadFile = File(...),  # noqa: B008 — standard FastAPI upload pattern
) -> UploadResponse:
    # Read one byte past the limit so an oversized file is rejected without loading all of it.
    content = file.file.read(settings.MAX_CSV_UPLOAD_BYTES + 1)
    if len(content) > settings.MAX_CSV_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"CSV file exceeds the {settings.MAX_CSV_UPLOAD_BYTES // (1024 * 1024)} MB limit",
        )
    service = MarketDataService(db)
    asset, written = service.upload_csv(
        symbol.upper(),
        content,
        asset_type=asset_type,
        exchange=exchange,
        sector=sector,
        industry=industry,
        market_cap_cr=market_cap_cr,
        overwrite=user.role == UserRole.ADMIN,  # shared data: only admins may replace existing bars
        synthetic=synthetic,
    )
    return UploadResponse(asset=AssetRead.model_validate(asset), bars_written=written)


@router.get("/{symbol}/data", response_model=OhlcvSeriesResponse)
def get_ohlcv(symbol: str, start_date: date, end_date: date, user: CurrentUser, db: DbSession) -> OhlcvSeriesResponse:
    service = MarketDataService(db)
    bars = service.get_ohlcv(symbol.upper(), start_date, end_date)
    return OhlcvSeriesResponse(symbol=symbol.upper(), bars=bars)
