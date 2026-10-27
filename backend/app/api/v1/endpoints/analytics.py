from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.backtest import CompareRequest, CompareResponse
from app.schemas.optimizer import OptimizeRequest, OptimizeResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/compare", response_model=CompareResponse)
def compare_backtests(payload: CompareRequest, user: CurrentUser, db: DbSession) -> CompareResponse:
    return AnalyticsService(db).compare(payload.backtest_ids, user)


@router.post("/optimize-portfolio", response_model=OptimizeResponse)
def optimize_portfolio_endpoint(payload: OptimizeRequest, user: CurrentUser, db: DbSession) -> OptimizeResponse:
    return AnalyticsService(db).optimize(
        payload.symbols, payload.start_date, payload.end_date, payload.method, payload.risk_free_rate
    )
