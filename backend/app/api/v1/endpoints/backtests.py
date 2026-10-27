from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import CurrentUser, DbSession, PageNumber, PageSize
from app.core.config import settings
from app.models.backtest import BacktestStatus
from app.repositories.backtest import TradeRepository
from app.schemas.backtest import (
    BacktestCreate,
    BacktestEquityRead,
    BacktestMetricsRead,
    BacktestRead,
    BacktestStatusRead,
    CostSensitivityEntry,
    WalkForwardWindow,
)
from app.schemas.common import Message, Page
from app.schemas.trade import TradeRead
from app.services.audit_service import AuditService
from app.services.backtest_service import BacktestService
from app.tasks.backtest_tasks import dispatch_backtest
from app.utils.exceptions import ValidationFailedError

router = APIRouter(prefix="/backtests", tags=["backtests"])
limiter = Limiter(key_func=get_remote_address)


@router.post("", response_model=BacktestRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_BACKTEST_CREATE)
def create_backtest(request: Request, payload: BacktestCreate, user: CurrentUser, db: DbSession) -> BacktestRead:
    backtest = BacktestService(db).create(user.id, payload)
    AuditService(db).record(
        user_id=user.id,
        action="backtest.create",
        resource_type="backtest",
        resource_id=backtest.id,
        details={"symbols": backtest.symbols, "strategy_id": backtest.strategy_id},
        ip_address=request.client.host if request.client else None,
    )
    dispatch_backtest(backtest.id)
    return BacktestRead.model_validate(backtest)


@router.get("", response_model=Page[BacktestRead])
def list_backtests(
    user: CurrentUser, db: DbSession, page: PageNumber = 1, page_size: PageSize = 20
) -> Page[BacktestRead]:
    service = BacktestService(db)
    items, total = service.list_for_owner(user.id, (page - 1) * page_size, page_size)
    return Page.create([BacktestRead.model_validate(b) for b in items], total, page, page_size)


@router.get("/{backtest_id}", response_model=BacktestRead)
def get_backtest(backtest_id: int, user: CurrentUser, db: DbSession) -> BacktestRead:
    backtest = BacktestService(db).get_owned(backtest_id, user)
    return BacktestRead.model_validate(backtest)


@router.get("/{backtest_id}/status", response_model=BacktestStatusRead)
def get_backtest_status(backtest_id: int, user: CurrentUser, db: DbSession) -> BacktestStatusRead:
    backtest = BacktestService(db).get_owned(backtest_id, user)
    return BacktestStatusRead(
        id=backtest.id,
        status=backtest.status,
        error_message=backtest.error_message,
        runtime_seconds=backtest.runtime_seconds,
    )


@router.get("/{backtest_id}/metrics", response_model=BacktestMetricsRead)
def get_backtest_metrics(backtest_id: int, user: CurrentUser, db: DbSession) -> BacktestMetricsRead:
    backtest = BacktestService(db).get_owned(backtest_id, user)
    if backtest.status != BacktestStatus.COMPLETED or backtest.result is None:
        raise ValidationFailedError(f"Backtest is '{backtest.status.value}', metrics are not available yet")
    return BacktestMetricsRead.model_validate(backtest.result, from_attributes=True)


@router.get("/{backtest_id}/equity", response_model=BacktestEquityRead)
def get_backtest_equity(backtest_id: int, user: CurrentUser, db: DbSession) -> BacktestEquityRead:
    backtest = BacktestService(db).get_owned(backtest_id, user)
    if backtest.status != BacktestStatus.COMPLETED or backtest.result is None:
        raise ValidationFailedError(f"Backtest is '{backtest.status.value}', results are not available yet")
    return BacktestEquityRead.model_validate(backtest.result, from_attributes=True)


@router.get("/{backtest_id}/trades", response_model=list[TradeRead])
def get_backtest_trades(backtest_id: int, user: CurrentUser, db: DbSession) -> list[TradeRead]:
    backtest = BacktestService(db).get_owned(backtest_id, user)
    trades = TradeRepository(db).list_for_backtest(backtest.id)
    return [TradeRead.model_validate(t) for t in trades]


@router.get("/{backtest_id}/cost-sensitivity", response_model=list[CostSensitivityEntry])
def get_cost_sensitivity(backtest_id: int, user: CurrentUser, db: DbSession) -> list[CostSensitivityEntry]:
    """Re-runs the backtest's exact signals at 0x/0.5x/1x/1.5x/2x its transaction
    costs, so the reported return can be read alongside how sensitive it is to
    the cost assumptions rather than as an isolated, cost-cherry-picked number."""
    entries = BacktestService(db).analyze_cost_sensitivity(backtest_id, user)
    return [CostSensitivityEntry(**e) for e in entries]


@router.get("/{backtest_id}/walk-forward", response_model=list[WalkForwardWindow])
def get_walk_forward_validation(
    backtest_id: int, user: CurrentUser, db: DbSession, n_windows: int = 4
) -> list[WalkForwardWindow]:
    """Splits the backtest period into `n_windows` contiguous windows and re-runs
    the same fixed strategy parameters on each — walk-forward *validation* (checking
    consistency across regimes), not walk-forward *optimization* (no parameter
    re-search per window)."""
    windows = BacktestService(db).run_walk_forward_validation(backtest_id, user, n_windows=n_windows)
    return [WalkForwardWindow(**w) for w in windows]


@router.delete("/{backtest_id}", response_model=Message)
def delete_backtest(request: Request, backtest_id: int, user: CurrentUser, db: DbSession) -> Message:
    BacktestService(db).delete(backtest_id, user)
    AuditService(db).record(
        user_id=user.id,
        action="backtest.delete",
        resource_type="backtest",
        resource_id=backtest_id,
        ip_address=request.client.host if request.client else None,
    )
    return Message(message="Backtest deleted")
